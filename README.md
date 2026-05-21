# GPU Finder

GPU Finder attempts to make it easier to find and provision Compute Engine Instances with GPUs.

## Why GPU Finder?

GPU quotas are not always consistent across regions and at any particular time. At peak times, there may be limited availability of GPUs in the cloud due to high demand for their compute capacity. This makes finding and provisioning of GPUs difficult and time consuming. By just setting a few configuration parameters, this script can be used to automate the process of finding and provisioning Compute Engine instances with GPUs.

## Prerequisites

* A GCP account and access to a service account with the permissions needed for creating instances. See the [docs](https://cloud.google.com/docs/authentication/production#passing_variable) for creating a key file and setting the ```GOOGLE_APPLICATION_CREDENTIALS``` environment variable
* A python environment with ```google-api-python-client==2.0.2``` library installed using pip

## Using the GPU Finder

1. Download the service account key file and set the ```GOOGLE_APPLICATION_CREDENTIALS``` environment variable to authenticate with GCP APIs
2. Install the Google API client library by running the command below:
```bash
pip install -r requirements.txt
```` 
3. Modify the `gpu-config.json` file to set the appropriate configuration parameters. In addition to the name of the machine, the important parameters to set are:
 * number_of_instances: Number of instances to create
 * machine_type: [The type of Compute Engine machine(s) to create](https://cloud.google.com/compute/docs/machine-types)
 * zone: [A list of zones to attempt to create instances in](https://cloud.google.com/compute/docs/regions-zones). To attempt all zones, leave the list blank (i.e. empty brackets [] will look for instances in all zones)

| Zone                      | Location	                                    | GPU model	                | GPU virtual workstation |
|---------------------------|----------------------------------------------|---------------------------|-------------------------|
| asia-east1-a              |	Changhua County, Taiwan, APAC	               | T4, P100, K80.            |	T4, P100                |
| asia-east1-b              |	Changhua County, Taiwan, APAC	               | K80                       |                         |
| asia-east1-c              |	Changhua County, Taiwan, APAC	               | T4, V100, P100            |	T4, P100                |
| asia-east2-a              |                                              |                           |                         |
| asia-east2-b              |                                              |                           |                         |
| asia-east2-c              |	Hong Kong, APAC			                     |                           |                         |
| asia-northeast1-a         |                                              |                           |                         |
| asia-northeast1-c         |	Tokyo, Japan, APAC	                        | T4                        |	T4                      |
| asia-northeast1-b         |	Tokyo, Japan, APAC			                  |                           |                         |
| asia-northeast2-a         |                                              |                           |                         |
| asia-northeast2-b         |                                              |                           |                         |
| asia-northeast2-c         |	Osaka, Japan, APAC	                        |                           |                         |
| asia-northeast3-a         |	Seoul, South Korea, APAC	                  |                           |                         |
| asia-northeast3-b         |                                              |                           |                         |
| asia-northeast3-c         |	Seoul, South Korea, APAC	                  | T4                        |	T4                      |
| asia-south1-a             |                                              |                           |                         |
| asia-south1-b             |	Mumbai, India, APAC	                        | T4                        |	T4                      |
| asia-south1-c             |	Mumbai, India, APAC	                        |                           |                         |
| asia-southeast1-a         |	Jurong West, Singapore, APAC	               | T4                        |	T4                      |
| asia-southeast1-b         |	Jurong West, Singapore, APAC	               | T4, P4                    |	T4, P4                  |
| asia-southeast1-c         |	Jurong West, Singapore, APAC	               | A100, T4, P4              |	T4, P4                  |
| asia-southeast2-a         |                                              |                           |                         |
| asia-southeast2-b         |	Jakarta, Indonesia, APAC	                  | T4                        |	T4                      |
| asia-southeast2-c         |	Jakarta, Indonesia, APAC	                  |                           |                         |
| australia-southeast1-a    |	Sydney, Australia, APAC	                     | T4, P4                    |	T4, P4                  |
| australia-southeast1-b    |	Sydney, Australia, APAC	                     | P4                        |	P4                      |
| australia-southeast1-c    |	Sydney, Australia, APAC	                     | P100                      |	P100                    |
| europe-north1-a           |                                              |                           |                         |
| europe-north1-b           |                                              |                           |                         |
| europe-north1-c           |	Hamina, Finland, Europe	                     |                           |                         |
| europe-west1-b            |	St. Ghislain, Belgium, Europe	               | P100, K80                 |	P100                    |
| europe-west1-c            |	St. Ghislain, Belgium, Europe	               |                           |                         |
| europe-west1-d            |	St. Ghislain, Belgium, Europe	               | P100, K80                 |	P100                    |
| europe-west2-a            |                                              |                           |                         |
| europe-west2-b            |	London, England, Europe	                     | T4                        |	T4                      |
| europe-west2-c            |	London, England, Europe	                     |                           |                         |
| europe-west3-a            |	Frankfurt, Germany, Europe	                  |                           |                         |
| europe-west3-b            |	Frankfurt, Germany, Europe	                  | T4                        |	T4                      |
| europe-west3-c            |	Frankfurt, Germany, Europe	                  |                           |                         |
| europe-west4-a            |	Eemshaven, Netherlands, Europe	            | A100, V100, P100          |	P100                    |
| europe-west4-b            |	Eemshaven, Netherlands, Europe	            | A100, T4, P4, V100        |	T4, P4                  |
| europe-west4-c            |	Eemshaven, Netherlands, Europe	            | T4, P4, V100	             | T4, P4                  |
| europe-west6-a            |                                              |                           |                         |
| europe-west6-b            |                                              |                           |                         |
| europe-west6-c            |	Zurich, Switzerland, Europe	               |                           |                         |
| northamerica-northeast1-a |                                              |                           |                         |
| northamerica-northeast1-b |                                              |                           |                         |
| northamerica-northeast1-c |	Montréal, Québec, North America	            | P4                        |	P4                      |
| southamerica-east1-a      |                                              |                           |                         |
| southamerica-east1-b      |	Osasco, São Paulo, Brazil, South America     |                           |                         |
| southamerica-east1-c      |	Osasco, São Paulo, Brazil, South America     | T4                        |	T4                      |
| us-central1-a             |	Council Bluffs, Iowa, North America          | A100, T4, P4, V100, K80   |	T4, P4                  |
| us-central1-b             |	Council Bluffs, Iowa, North America          | A100, T4, V100            |	T4                      |
| us-central1-c             |	Council Bluffs, Iowa, North America          | A100, P4, V100, P100, K80 |	P4, P100                |
| us-central1-f             |	Council Bluffs, Iowa, North America          | T4, V100, P100, K80       |	T4, P100                |
| us-east1-b                |	Moncks Corner, South Carolina, North America	| P100                      |	P100                    |
| us-east1-c                |	Moncks Corner, South Carolina, North America	| T4, V100, P100, K80       |	T4, P100                |
| us-east1-d                |	Moncks Corner, South Carolina, North America	| T4, K80                   |	T4                      |
| us-east4-a                |	Ashburn, Virginia, North America             | P4	                      | P4                      |
| us-east4-b                |	Ashburn, Virginia, North America             | T4, P4                    |	T4, P4                  |
| us-east4-c                |	Ashburn, Virginia, North America             | P4                        |	P4                      |
| us-west1-a                |	The Dalles, Oregon, North America            | T4, V100, P100            |	T4                      |
| us-west1-b                |	The Dalles, Oregon, North America            | T4, V100, P100, K80       |	T4, P100                |
| us-west1-c                |	The Dalles, Oregon, North America            |                           |                         |
| us-west2-a                |	Los Angeles, California, North America       |                           |                         |
| us-west2-b                |                                              |                           |                         |
| us-west2-c                |	Los Angeles, California, North America       | P4                        |	P4                      |
| us-west3-a                |                                              |                           |                         |
| us-west3-b                |                                              |                           |                         |
| us-west3-c                |	Salt Lake City, Utah, North America          |                           |                         |
| us-west4-a                |                                              |                           |                         |
| us-west4-b                |                                              |                           |                         |
| us-west4-c                |	Las Vegas, Nevada, North America             |                           |                         |

 * gpu_type: [The type of GPU to use](https://cloud.google.com/compute/docs/gpus). Note that newer accelerator-optimized machine types (like A2, A3, A4, G2, and G4) come with GPUs intrinsically attached. You must use the correct machine type family for the desired GPU model. The older GPU types can be attached to N1 machine types.
 * number_of_gpus: [The number of GPUs to attach to each instance](https://cloud.google.com/compute/docs/gpus). This must match the configured machine type when using accelerator-optimized instances.

| GPU Model                   | Configuration Name        | Compatible Machine Types  | Number of GPUs |
|-----------------------------|---------------------------|---------------------------|----------------|
| NVIDIA® GB300 (A4X Max)     | nvidia-gb300              | A4X Max                   | 4              |
| NVIDIA® GB200 (A4X)         | nvidia-gb200              | A4X                       | 4              |
| NVIDIA® B200 (A4)           | nvidia-b200               | A4                        | 8              |
| NVIDIA® H200 (A3 Ultra)     | nvidia-h200-141gb         | A3 Ultra                  | 8              |
| NVIDIA® H100 (A3 Mega/High/Edge) | nvidia-h100-mega-80gb / nvidia-h100-80gb | A3        | 1, 2, 4, 8     |
| NVIDIA® A100 80GB (A2 Ultra)| nvidia-a100-80gb          | A2 Ultra                  | 1, 2, 4, 8     |
| NVIDIA® A100 (A2 Standard)  | nvidia-tesla-a100         | A2                        | 1, 2, 4, 8, 16 |
| NVIDIA® RTX PRO 6000 (G4)   | nvidia-rtx-pro-6000       | G4                        | 1, 2, 4, 8     |
| NVIDIA® L4 (G2)             | nvidia-l4                 | G2                        | 1, 2, 4, 8     |
| NVIDIA® T4                  | nvidia-tesla-t4           | N1                        | 1, 2, 4        |
| NVIDIA® V100                | nvidia-tesla-v100         | N1                        | 1, 2, 4, 8     |
| NVIDIA® P4                  | nvidia-tesla-p4           | N1                        | 1, 2, 4        |
| NVIDIA® P100                | nvidia-tesla-p100         | N1                        | 1, 2, 4        |
| NVIDIA® K80                 | nvidia-tesla-k80          | N1                        | 1, 2, 4, 8     |

4. Additional configuration like disk type, disk size, firewall rules, image type, image family, VPC, startup scripts, and others can be set in the configuration file too.
5. When running the script, you will see output in the logs about which regions and zones the instances will be created in, the names of instances, and whether a quota has been reached in a given region.

## Clean Up
There is a `delete_instance` function in the script that will delete the instances passed in the `instance_details` parameter. Please be mindful of cleaning up instances with GPUs attached when these are no longer needed.

## Modern GCE Constraints & Key Lessons

Modern GCP environments and newer machine/GPU families introduce strict constraints and hardware requirements that must be handled during provisioning.

### 1. Handling Modern GCE Constraints

* **`constraints/compute.requireShieldedVm`**: Many modern enterprise folders or projects enforce this organizational policy. To prevent creation failures, GPU Finder automatically configures every instance with `shieldedInstanceConfig` (enabling Secure Boot, vTPM, and Integrity Monitoring by default).
* **`constraints/compute.vmExternalIpAccess`**: To meet security standards, organizations frequently block public external IP addresses. GPU Finder implements the `assign_external_ip` parameter to circumvent policy violations. By setting `"assign_external_ip": false`, instances are created without an external NAT IP.

### 2. New Parameters in `gpu-config.json`

Ensure your configuration files are updated with these modern settings:

* **`assign_external_ip`** *(boolean)*: Controls the attachment of a public external ephemeral NAT IP to the instance. Set to `false` in highly secure or constrained environments.
* **`disk_type`** *(string)*: Specifies the type of boot/root persistent disk. Modern architectures (such as `g4-standard-*` and `g2-standard-*`) require higher-performance disk backends like `hyperdisk-balanced` or `pd-balanced`.

### 3. Hyperdisk Requirements for Modern Instances

* **G4 & Modern GPU Families**: Newer machine types, such as G4 (equipped with NVIDIA® RTX PRO 6000) and G2 (equipped with NVIDIA® L4), have strict dependencies on modern storage technologies. 
* Attempting to use legacy or standard persistent disks (`pd-standard`) with these instances will result in provisioning failures. Ensure you set `"disk_type": "hyperdisk-balanced"` when defining configuration payloads for these machine types to ensure successful, policy-compliant deployment.
