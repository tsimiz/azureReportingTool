"""Module for fetching data from Azure environment."""

import logging
from typing import Dict, List, Any
from azure.identity import DefaultAzureCredential, ClientSecretCredential
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.storage import StorageManagementClient

logger = logging.getLogger(__name__)


class AzureFetcher:
    """Fetches data from Azure environment."""

    def __init__(self, subscription_id: str, tenant_id: str = None, 
                 client_id: str = None, client_secret: str = None):
        """Initialize Azure clients with credentials."""
        self.subscription_id = subscription_id
        
        # Use ClientSecretCredential if credentials provided, else DefaultAzureCredential
        if tenant_id and client_id and client_secret:
            self.credential = ClientSecretCredential(
                tenant_id=tenant_id,
                client_id=client_id,
                client_secret=client_secret
            )
        else:
            self.credential = DefaultAzureCredential()
        
        # Initialize Azure clients
        self.resource_client = ResourceManagementClient(
            self.credential, subscription_id
        )
        self.compute_client = ComputeManagementClient(
            self.credential, subscription_id
        )
        self.network_client = NetworkManagementClient(
            self.credential, subscription_id
        )
        self.storage_client = StorageManagementClient(
            self.credential, subscription_id
        )
        
        logger.info(f"Azure clients initialized for subscription: {subscription_id}")

    def fetch_resource_groups(self) -> List[Dict[str, Any]]:
        """Fetch all resource groups."""
        logger.info("Fetching resource groups...")
        resource_groups = []
        
        try:
            for rg in self.resource_client.resource_groups.list():
                resource_groups.append({
                    'name': rg.name,
                    'location': rg.location,
                    'id': rg.id,
                    'tags': rg.tags or {}
                })
            logger.info(f"Found {len(resource_groups)} resource groups")
        except Exception as e:
            logger.error(f"Error fetching resource groups: {e}")
            
        return resource_groups

    def fetch_virtual_machines(self) -> List[Dict[str, Any]]:
        """Fetch all virtual machines."""
        logger.info("Fetching virtual machines...")
        vms = []
        
        try:
            for vm in self.compute_client.virtual_machines.list_all():
                vm_details = {
                    'name': vm.name,
                    'location': vm.location,
                    'id': vm.id,
                    'resource_group': vm.id.split('/')[4],
                    'vm_size': vm.hardware_profile.vm_size,
                    'os_type': vm.storage_profile.os_disk.os_type,
                    'tags': vm.tags or {}
                }
                
                # Get instance view for status
                try:
                    rg_name = vm.id.split('/')[4]
                    instance_view = self.compute_client.virtual_machines.instance_view(
                        rg_name, vm.name
                    )
                    statuses = [status.code for status in instance_view.statuses]
                    vm_details['statuses'] = statuses
                except Exception as e:
                    logger.warning(f"Could not get instance view for {vm.name}: {e}")
                    vm_details['statuses'] = []
                
                vms.append(vm_details)
                
            logger.info(f"Found {len(vms)} virtual machines")
        except Exception as e:
            logger.error(f"Error fetching virtual machines: {e}")
            
        return vms

    def fetch_storage_accounts(self) -> List[Dict[str, Any]]:
        """Fetch all storage accounts."""
        logger.info("Fetching storage accounts...")
        storage_accounts = []
        
        try:
            for sa in self.storage_client.storage_accounts.list():
                storage_accounts.append({
                    'name': sa.name,
                    'location': sa.location,
                    'id': sa.id,
                    'resource_group': sa.id.split('/')[4],
                    'sku': sa.sku.name,
                    'kind': sa.kind,
                    'https_only': sa.enable_https_traffic_only,
                    'public_network_access': getattr(sa, 'public_network_access', 'Enabled'),
                    'tags': sa.tags or {}
                })
            logger.info(f"Found {len(storage_accounts)} storage accounts")
        except Exception as e:
            logger.error(f"Error fetching storage accounts: {e}")
            
        return storage_accounts

    def fetch_network_security_groups(self) -> List[Dict[str, Any]]:
        """Fetch all network security groups."""
        logger.info("Fetching network security groups...")
        nsgs = []
        
        try:
            for nsg in self.network_client.network_security_groups.list_all():
                nsg_details = {
                    'name': nsg.name,
                    'location': nsg.location,
                    'id': nsg.id,
                    'resource_group': nsg.id.split('/')[4],
                    'tags': nsg.tags or {},
                    'security_rules': []
                }
                
                # Add security rules
                if nsg.security_rules:
                    for rule in nsg.security_rules:
                        nsg_details['security_rules'].append({
                            'name': rule.name,
                            'priority': rule.priority,
                            'direction': rule.direction,
                            'access': rule.access,
                            'protocol': rule.protocol,
                            'source_address_prefix': rule.source_address_prefix,
                            'destination_address_prefix': rule.destination_address_prefix,
                            'destination_port_range': rule.destination_port_range
                        })
                
                nsgs.append(nsg_details)
                
            logger.info(f"Found {len(nsgs)} network security groups")
        except Exception as e:
            logger.error(f"Error fetching network security groups: {e}")
            
        return nsgs

    def fetch_virtual_networks(self) -> List[Dict[str, Any]]:
        """Fetch all virtual networks."""
        logger.info("Fetching virtual networks...")
        vnets = []
        
        try:
            for vnet in self.network_client.virtual_networks.list_all():
                vnet_details = {
                    'name': vnet.name,
                    'location': vnet.location,
                    'id': vnet.id,
                    'resource_group': vnet.id.split('/')[4],
                    'address_space': vnet.address_space.address_prefixes,
                    'subnets': [],
                    'tags': vnet.tags or {}
                }
                
                # Add subnet information
                if vnet.subnets:
                    for subnet in vnet.subnets:
                        vnet_details['subnets'].append({
                            'name': subnet.name,
                            'address_prefix': subnet.address_prefix
                        })
                
                vnets.append(vnet_details)
                
            logger.info(f"Found {len(vnets)} virtual networks")
        except Exception as e:
            logger.error(f"Error fetching virtual networks: {e}")
            
        return vnets

    def _extract_resource_group_from_id(self, resource_id: str) -> str:
        """Extract resource group name from Azure resource ID.
        
        Azure resource IDs follow the pattern:
        /subscriptions/{subscription-id}/resourceGroups/{resource-group-name}/...
        """
        try:
            parts = resource_id.split('/')
            # Find 'resourceGroups' in the path and get the next element
            for i, part in enumerate(parts):
                if part.lower() == 'resourcegroups' and i + 1 < len(parts):
                    return parts[i + 1]
            return 'Unknown'
        except Exception as e:
            logger.warning(f"Could not extract resource group from ID {resource_id}: {e}")
            return 'Unknown'

    def fetch_generic_resources(self) -> List[Dict[str, Any]]:
        """Fetch all resources in the subscription using the generic resources API."""
        logger.info("Fetching all resources in subscription...")
        all_resources = []
        
        try:
            for resource in self.resource_client.resources.list():
                all_resources.append({
                    'name': resource.name,
                    'type': resource.type,
                    'location': resource.location,
                    'id': resource.id,
                    'resource_group': self._extract_resource_group_from_id(resource.id),
                    'tags': resource.tags or {},
                    'kind': getattr(resource, 'kind', None),
                    'sku': getattr(resource, 'sku', None)
                })
            logger.info(f"Found {len(all_resources)} total resources")
        except Exception as e:
            logger.error(f"Error fetching generic resources: {e}")
            
        return all_resources

    def fetch_all_resources(self) -> Dict[str, List[Dict[str, Any]]]:
        """Fetch all Azure resources."""
        logger.info("Starting to fetch all Azure resources...")
        
        resources = {
            'resource_groups': self.fetch_resource_groups(),
            'virtual_machines': self.fetch_virtual_machines(),
            'storage_accounts': self.fetch_storage_accounts(),
            'network_security_groups': self.fetch_network_security_groups(),
            'virtual_networks': self.fetch_virtual_networks(),
            'all_resources': self.fetch_generic_resources()
        }
        
        logger.info("Completed fetching all Azure resources")
        return resources
