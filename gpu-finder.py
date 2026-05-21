#!/usr/bin/env python

# Copyright 2015 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Example of using the Compute Engine API to create and delete instances.
Creates a new compute engine instance and uses it to apply a caption to
an image.
    https://cloud.google.com/compute/docs/tutorials/python-guide
For more information, see the README.md under /compute.
"""

import time
import json
import re
import os
import copy
import googleapiclient.discovery

def load_state():
    if os.path.exists('gpu-finder-state.json'):
        try:
            with open('gpu-finder-state.json', 'r') as f:
                return json.load(f)
        except Exception:
            return {"instances": []}
    return {"instances": []}

def save_state(state):
    with open('gpu-finder-state.json', 'w') as f:
        json.dump(state, f, indent=4)

def verify_and_get_active_instances(compute, project, base_name, state):
    active_instances = []
    updated_instances = []
    for instance in state.get("instances", []):
        if instance.get("project") == project and (instance.get("name") == base_name or instance.get("name", "").startswith(base_name + "-")):
            try:
                res = compute.instances().get(
                    project=project,
                    zone=instance["zone"],
                    instance=instance["name"]
                ).execute()
                status = res.get("status")
                if status in ("PROVISIONING", "STAGING", "RUNNING"):
                    active_instances.append(instance)
                    updated_instances.append(instance)
            except Exception:
                pass
        else:
            updated_instances.append(instance)
    state["instances"] = updated_instances
    save_state(state)
    return active_instances

def check_gpu_config(config):
    compute_config = config
    machine_type = compute_config['instance_config']['machine_type']

    match = re.search(r'(?:highgpu|ultragpu|megagpu|edgegpu|standard)-(\d+)(?:g|metal)?', machine_type)

    # For G2 and G4 standard machine types, the number represents vCPUs, not GPUs.
    # We skip strict GPU count matching for standard machine types for now to avoid breaking the script.
    if match and 'standard' not in machine_type:
        number_of_gpus_requested = compute_config['instance_config']['number_of_gpus']
        gpus_in_machine_type = match.group(1)
        if number_of_gpus_requested != int(gpus_in_machine_type):
            raise Exception("Please match the number of GPUs parameter with the correct machine type in the config file")

def get_zone_info(compute, project):
    zone_list = []
    request = compute.zones().list(project=project)
    while request is not None:
        response = request.execute()
        for zone in response.get('items', []):
            if zone['status'] == 'UP':
                zone_regions = {
                    'region': zone['name'].rsplit('-', 1)[0],
                    'zone': zone['name']
                }
                zone_list.append(zone_regions)
        request = compute.zones().list_next(previous_request=request, previous_response=response)
    return zone_list

def check_machine_type_and_accelerator(compute, project, machine_type, gpu_type, zones):
    zone_list = zones
    available_zones = []
    for zone in zone_list:
        request = compute.machineTypes().list(project=project, zone=zone['zone'])
        while request is not None:
            response = request.execute()
            for machine in response.get('items', []):
                if 'accelerators' in machine and machine['name'] == machine_type and machine['accelerators'][0]['guestAcceleratorType'] == gpu_type:
                    zones_with_instances = {
                        'machine_type': machine['name'],
                        'region': zone['region'],
                        'zone': zone['zone'],
                        'guest_cpus': machine['guestCpus'],
                        'description': machine['description'],
                        'accelerators': machine['accelerators']
                    }
                    available_zones.append(zones_with_instances)
                elif machine['name'] == machine_type:
                    zones_with_instances = {
                        'machine_type': machine['name'],
                        'region': zone['region'],
                        'zone': zone['zone'],
                        'guest_cpus': machine['guestCpus'],
                        'description': machine['description']
                    }
                    available_zones.append(zones_with_instances)
            request = compute.machineTypes().list_next(previous_request=request, previous_response=response)
    if not available_zones:
        raise Exception(f"No machine types of {machine_type} are available")
    return available_zones

def get_accelerator_quota(compute, project, config, zone, requested_gpus):
    zone_list = zone
    accelerator_list = []
    for i in zone_list:
        request = compute.acceleratorTypes().list(project=project, zone=i['zone'])
        while request is not None:
            response = request.execute()
            if 'items' in response:
                for accelerator in response.get('items', []):
                    if accelerator['name'] == config['instance_config']['gpu_type']:
                        if requested_gpus <= accelerator['maximumCardsPerInstance']:
                            accelerator_dict = {
                                "region": i['region'],
                                "zone": i['zone'],
                                "machine_type": i['machine_type'],
                                "guest_cpus": i['guest_cpus'],
                                "name": accelerator['name'],
                                "description": accelerator['description'],
                                "maximum number of GPUs per instance": accelerator['maximumCardsPerInstance']
                            }
                            accelerator_list.append(accelerator_dict)
                            print(f"{requested_gpus} GPUs requested per instance, {i['zone']} has {accelerator['name']} GPUs with a maximum of {accelerator['maximumCardsPerInstance']} per instance")
                        else:
                            print(
                                f"{requested_gpus} GPUs requested per instance, {i['zone']} doesn't have enough GPUs, with a maximum of {accelerator['maximumCardsPerInstance']} per instance")
            request = compute.acceleratorTypes().list_next(previous_request=request, previous_response=response)
    if not accelerator_list:
        raise Exception(f"No accelerator types of {config['instance_config']['gpu_type']} are available with {config['instance_config']['machine_type']} in any zone, or wrong number of GPUs requested")
    return accelerator_list


def create_instance(compute, project, config, zone_list):
    compute_config = config
    regions_to_try = list({v['region'] for v in zone_list})
    created_instances = []
    instances = 0
    regions_attempted = 0
    print(f"There are {len(regions_to_try)} regions to try that match the GPU type and machine type configuration.")
    for region in regions_to_try:
        print(f"Attempting to create instances in {region}")
        zones = [z for z in zone_list if z['region'] == region]
        print(f"There are {len(zones)} zones to try in {region}")
        zones_attempted = 0
        move_regions = 0
        for i in range(len(zones)):
            zone_config = zones[i]
            for j in range(compute_config['number_of_instances']):
                print(f"Creating instance number {instances+1} of {compute_config['number_of_instances']} in {zone_config['zone']}, zone {zones_attempted+1} out of {len(zones)} attempted.")
                image_project = compute_config['instance_config']['image_project']
                image_family = compute_config['instance_config']['image_family']
                image_response = compute.images().getFromFamily(
                    project=image_project, family=image_family).execute()
                source_disk_image = image_response['selfLink']
                instance_name = compute_config['instance_config']['name'] + '-' + str(instances+1) + '-' + zone_config['zone']
                # Configure the machine
                machine_type = f"zones/{zone_config['zone']}/machineTypes/{compute_config['instance_config']['machine_type']}"
                # startup_script = open(
                #     os.path.join(
                #         os.path.dirname(__file__), 'startup-script.sh'), 'r').read()
                # image_url = "http://storage.googleapis.com/gce-demo-input/photo.jpg"
                # image_caption = "Ready for dessert?"

                is_preemptible = compute_config.get('preemptible', False)

                network_interface = {
                    'kind': 'compute#networkInterface',
                    'network': compute_config['instance_config']['network_interfaces']['network'],
                    'aliasIpRanges': []
                }
                if compute_config['instance_config'].get('assign_external_ip', True):
                    network_interface['accessConfigs'] = [
                        {
                            'kind': 'compute#accessConfig',
                            'name': 'External NAT',
                            'type': 'ONE_TO_ONE_NAT',
                            'networkTier': 'PREMIUM'
                        }
                    ]

                config = {
                    'name': instance_name,
                    'machineType': machine_type,

                    # Specify the boot disk and the image  to use as a source.
                    'disks': [
                        {
                            'kind': 'compute#attachedDisk',
                            'type': 'PERSISTENT',
                            'boot': True,
                            'mode': 'READ_WRITE',
                            'autoDelete': True,
                            'deviceName': compute_config['instance_config']['name'],
                            'initializeParams': {
                                'sourceImage': source_disk_image,
                                'diskType': f"projects/{project}/zones/{zone_config['zone']}/diskTypes/{compute_config['instance_config']['disk_type']}",
                                'diskSizeGb': compute_config['instance_config']['disk_size'],
                                'labels': {}
                            },
                            "diskEncryptionKey": {}
                        }
                    ],
                    'canIpForward': False,
                    'guestAccelerators': [
                        {
                            'acceleratorCount': compute_config['instance_config']['number_of_gpus'],
                            'acceleratorType': f"zones/{zone_config['zone']}/acceleratorTypes/{compute_config['instance_config']['gpu_type']}"
                        }
                    ],

                    'tags': {
                        "items": compute_config['instance_config']['firewall_rules']
                    },

                    # Specify a network interface with NAT to access the public
                    # internet.
                    'networkInterfaces': [network_interface],
                    'description': '',
                    'labels': {},
                    'scheduling': {
                        'preemptible': is_preemptible,
                        'onHostMaintenance': 'TERMINATE',
                        'automaticRestart': not is_preemptible,
                        'nodeAffinities': []
                    },
                    'deletionProtection': False,
                    'reservationAffinity': {
                        'consumeReservationType': 'ANY_RESERVATION'
                    },
                    # Allow the instance to access cloud storage and logging.
                    'serviceAccounts': [{
                        'email': compute_config['instance_config']['identity_and_api_access']['service_account_email'],
                        'scopes': [
                            compute_config['instance_config']['identity_and_api_access']['scopes']
                        ]
                    }
                    ],
                    'shieldedInstanceConfig': {
                        'enableSecureBoot': True,
                        'enableVtpm': True,
                        'enableIntegrityMonitoring': True
                    },

                    'confidentialInstanceConfig': {
                        'enableConfidentialCompute': False
                    },

                    # Metadata is readable from the instance and allows you to
                    # pass configuration from deployment scripts to instances.
                    'metadata': {
                        'kind': 'compute#metadata',
                        'items': [],
                    }
                }

                print(f"Creating instance {instance_name}.")
                operation = compute.instances().insert(
                    project=project,
                    zone=zone_config['zone'],
                    body=config).execute()

                print('Waiting for operation to finish...')
                move_zones = 0
                while True:
                    result = compute.zoneOperations().get(
                        project=project,
                        zone=zone_config['zone'],
                        operation=operation['name']).execute()

                    if result['status'] == 'DONE':
                        print("done.")
                        if 'error' in result:
                            error_results = result['error']['errors']
                            if error_results[0]['code'] in ('QUOTA_EXCEEDED', 'ZONE_RESOURCE_POOL_EXHAUSTED', 'ZONE_RESOURCE_POOL_EXHAUSTED_WITH_DETAILS'):
                                move_regions = 1
                                print(Exception(result['error']))
                            else:
                                raise Exception(result['error'])
                        else:
                            instances += 1
                            move_regions = 0
                            print(f"Success: {instance_name} created")
                            print(f"{instances} created, {compute_config['number_of_instances']-instances} more to create")
                            instance_details = {
                                "name": instance_name,
                                "zone": zone_config['zone']
                            }
                            created_instances.append(instance_details)
                            # Save to state file immediately
                            state = load_state()
                            if "instances" not in state:
                                state["instances"] = []
                            state["instances"].append({
                                "name": instance_name,
                                "zone": zone_config['zone'],
                                "project": project
                            })
                            save_state(state)
                        break
                if instances >= compute_config['number_of_instances']:
                    print(f"Reached the desired number of instances")
                    break
                elif move_regions == 1:
                    print(f"Quota exceeded in region {region}, moving to next region")
                    break
            if instances >= compute_config['number_of_instances']:
                break
            elif move_regions == 1:
                break
            zones_attempted += 1
        regions_attempted += 1
        if instances >= compute_config['number_of_instances']:
            break
        elif regions_attempted >= len(regions_to_try):
            print(f"All regions attempted, there are not enough resources to create the desired {compute_config['number_of_instances']} instances, {instances} created")
            break
    return(created_instances)

def delete_instance(compute, project, instance_details):
    instances = instance_details
    print(f"Deleting {len(instances)} instances.")
    for i in range(len(instances)):
        instance = instances[i]
        zone = instance["zone"]
        name = instance["name"]

        print(f"Deleting instance {name}.")
        operation = compute.instances().delete(
            project=project,
            zone=zone,
            instance=name).execute()

        print('Waiting for operation to finish...')
        while True:
            result = compute.zoneOperations().get(
                project=project,
                zone=zone,
                operation=operation['name']).execute()

            if result['status'] == 'DONE':
                print("done.")
                if 'error' in result:
                    raise Exception(result['error'])
                state = load_state()
                if "instances" in state:
                    state["instances"] = [
                        inst for inst in state["instances"]
                        if not (inst.get("name") == name and inst.get("zone") == zone and inst.get("project") == project)
                    ]
                save_state(state)
                break

def create_instance_test(compute, project, config, zone, requested_gpus):
    zone_list = zone
    accelerator_list = []
    for i in zone_list:
        request = compute.acceleratorTypes().list(project=project, zone=i['zone'])
        while request is not None:
            response = request.execute()
            if 'items' in response:
                for accelerator in response['items']:
                    print(accelerator)


def main(gpu_config, wait=True):
    compute = googleapiclient.discovery.build('compute', 'v1')
    state = load_state()
    active_instances = verify_and_get_active_instances(compute, gpu_config["project_id"], gpu_config["instance_config"]["name"], state)
    
    local_config = copy.deepcopy(gpu_config)
    num_active = len(active_instances)
    remaining_instances = local_config['number_of_instances'] - num_active
    
    if remaining_instances <= 0:
        print(f"All {local_config['number_of_instances']} instances are already active. Skipping configuration.")
        return
        
    local_config['number_of_instances'] = remaining_instances

    if local_config["instance_config"]["zone"]:
        print(f"Processing selected zones from {local_config['instance_config']['zone']}")
        zone_info = get_zone_info(compute, local_config["project_id"])
        compute_zones = [z for z in zone_info if z['zone'] in local_config['instance_config']['zone']]
    else:
        print("Processing all zones")
        compute_zones = get_zone_info(compute, local_config["project_id"])
    check_gpu_config(local_config)
    # distinct_zones = list({v['zone'] for v in compute_zones})
    available_zones = check_machine_type_and_accelerator(compute, local_config["project_id"], local_config["instance_config"]["machine_type"], local_config["instance_config"]["gpu_type"], compute_zones)
    accelerators = get_accelerator_quota(compute, local_config["project_id"], local_config, available_zones, local_config["instance_config"]["number_of_gpus"])
    available_regions = list({v['region'] for v in available_zones})
    if available_regions:
        print(f"Machine type {local_config['instance_config']['machine_type']} is available in the following regions: {available_regions}")
        instance_details = create_instance(compute, local_config["project_id"], local_config, accelerators)
        all_instances = active_instances + instance_details
        if wait:
            print("hit enter to delete instances")
            input()
        delete_instance(compute, local_config["project_id"], all_instances)
    else:
        print(f"No regions available with the instance configuration {local_config['instance_config']['machine_type']} machine type and {local_config['instance_config']['gpu_type']} GPU type")

if __name__ == '__main__':
    with open('gpu-config.json', 'r') as f:
        gpu_config = json.load(f)
        
    failures = []
    
    if isinstance(gpu_config, list):
        for config in gpu_config:
            project_id = config.get('project_id')
            machine_type = config.get('instance_config', {}).get('machine_type')
            print(f"Processing configuration for project: {project_id} and machine type: {machine_type}")
            try:
                main(config)
            except Exception as e:
                print(f"Error processing configuration for project {project_id}, machine type {machine_type}: {e}")
                failures.append({
                    "project_id": project_id,
                    "machine_type": machine_type,
                    "error": str(e)
                })
    else:
        project_id = gpu_config.get('project_id')
        machine_type = gpu_config.get('instance_config', {}).get('machine_type')
        try:
            main(gpu_config)
        except Exception as e:
            print(f"Error processing configuration for project {project_id}, machine type {machine_type}: {e}")
            failures.append({
                "project_id": project_id,
                "machine_type": machine_type,
                "error": str(e)
            })
            
    if failures:
        print("\nSummary of failures:")
        for fail in failures:
            print(f"- Project: {fail['project_id']}, Machine Type: {fail['machine_type']}, Error: {fail['error']}")
    else:
        print("\nAll configurations processed successfully.")
