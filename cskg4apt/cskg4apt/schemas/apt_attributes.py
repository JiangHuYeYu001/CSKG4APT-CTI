from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class DiamondModelVertex(BaseModel):
	"""Diamond Model analysis vertex (Adversary/Capability/Infrastructure/Victim)"""

	adversary: Optional[str] = Field(default=None, description="Attacker / APT organization")
	capability: List[str] = Field(default_factory=list, description="Malware and tools used")
	infrastructure: List[str] = Field(default_factory=list, description="C2, domains, IPs")
	victim: List[str] = Field(default_factory=list, description="Target sectors/countries")
	timestamp: Optional[str] = Field(default=None, description="Event timestamp")
	event_id: Optional[str] = Field(default=None, description="Related event entity ID")


class APTThreatCard(BaseModel):
	"""APT organization threat intelligence card"""

	attacker_id: str = Field(..., description="APT organization entity ID")
	attacker_names: List[str] = Field(default_factory=list, description="Names and aliases")
	active_since: Optional[str] = Field(default=None, description="Active since date")
	attributed_to: Optional[str] = Field(default=None, description="Attributed country/region")

	# Tactical capabilities
	tactics: List[str] = Field(default_factory=list, description="MITRE ATT&CK tactics")
	techniques: List[str] = Field(default_factory=list, description="Specific techniques")

	# Known malware and tools
	malwares: List[str] = Field(default_factory=list, description="Known malware")
	tools: List[str] = Field(default_factory=list, description="Known tools")

	# Known infrastructure
	c2_servers: List[str] = Field(default_factory=list, description="C2 servers")
	domains: List[str] = Field(default_factory=list, description="Malicious domains")
	ips: List[str] = Field(default_factory=list, description="IP addresses")

	# Target information
	target_sectors: List[str] = Field(default_factory=list, description="Target sectors")
	target_countries: List[str] = Field(default_factory=list, description="Target countries")

	# Related CVEs
	exploited_cves: List[str] = Field(default_factory=list, description="Exploited CVEs")

	# Associations
	associated_groups: List[str] = Field(default_factory=list, description="Related APT groups")
	evidence_urls: List[str] = Field(default_factory=list, description="Evidence report URLs")

	# Threat score
	threat_level: Optional[str] = Field(default=None, description="High/Medium/Low")


class AttackChain(BaseModel):
	"""Attack chain based on MITRE Kill Chain"""

	attack_id: str = Field(..., description="Attack chain ID")
	attacker: Optional[str] = Field(default=None, description="APT organization")
	target: Optional[str] = Field(default=None, description="Attack target")
	timestamp: Optional[str] = Field(default=None, description="Attack time")

	# Kill Chain phases
	reconnaissance: Optional[Dict] = Field(default=None, description="Reconnaissance phase")
	weaponization: Optional[Dict] = Field(default=None, description="Weaponization phase")
	delivery: Optional[Dict] = Field(default=None, description="Delivery phase")
	exploitation: Optional[Dict] = Field(default=None, description="Exploitation phase")
	installation: Optional[Dict] = Field(default=None, description="Installation phase")
	command_control: Optional[Dict] = Field(default=None, description="C2 phase")
	actions_on_objective: Optional[Dict] = Field(default=None, description="Actions on objective")

	# Evidence
	evidence_source: Optional[str] = Field(default=None, description="Source text or URL")
	behaviors: List[str] = Field(default_factory=list, description="Associated behaviors/TTPs")
