import logging
import re
import time
from enum import Enum
from typing import Dict, FrozenSet, List, Optional, Set, Tuple

from pydantic import BaseModel, Field, field_validator, model_validator

logger = logging.getLogger(__name__)


class EntityType(str, Enum):
	"""CSKG4APT 12 entity types"""

	ATTACKER = "Attacker"
	INFRASTRUCTURE = "Infrastructure"
	MALWARE = "Malware"
	VULNERABILITY = "Vulnerability"
	ASSETS = "Assets"
	TARGET = "Target"
	EVENT = "Event"
	BEHAVIOR = "Behavior"
	TIME = "Time"
	TOOL = "Tool"
	CREDENTIAL = "Credential"
	INDICATOR = "Indicator"


class RelationType(str, Enum):
	"""CSKG4APT 7 relation types"""

	HAS = "has"
	USES = "uses"
	EXPLOIT = "exploit"
	EXIST = "exist"
	TARGET = "target"
	MEDIUM = "medium"
	BEHAVIOR = "behavior"


# ---------------------------------------------------------------------------
# Entity subtype constraints — keyword patterns that an entity name MUST
# match (at least one pattern in the list) for the given EntityType.
# Each value is a dict with:
#   "subtypes"  : human-readable subtype names (for documentation / prompts)
#   "patterns"  : compiled regexes – entity name must match >= 1 pattern
#   "keywords"  : lowercase keywords – entity name must contain >= 1 keyword
#   "anti_keywords" : if entity name contains ANY of these, reject it
#
# An entity passes validation if:
#   (matches any pattern OR contains any keyword) AND NOT contains any anti_keyword
# If both patterns and keywords are empty, no constraint is applied.
# ---------------------------------------------------------------------------

ENTITY_SUBTYPE_CONSTRAINTS: Dict[EntityType, dict] = {
	EntityType.ATTACKER: {
		"subtypes": [
			"APT group", "cybercrime gang", "hacktivist group",
			"insider threat actor", "state-sponsored actor", "threat actor alias",
		],
		"patterns": [
			re.compile(r"(?i)\bAPT[-\s]?\d+\b"),           # APT28, APT-29
			re.compile(r"(?i)\bTA\d+\b"),                   # TA505
			re.compile(r"(?i)\bFIN\d+\b"),                  # FIN7
			re.compile(r"(?i)\bUNC\d+\b"),                  # UNC2452
			re.compile(r"(?i)\bDEV[-\s]?\d+\b"),            # DEV-0537
		],
		"keywords": [
			"apt", "group", "gang", "team", "bear", "panda", "kitten", "spider",
			"typhoon", "sandstorm", "blizzard", "tempest", "sleet", "hail",
			"lazarus", "turla", "equation", "darkside", "revil", "lockbit",
			"conti", "blackcat", "alphv", "clop", "hive", "anonymous",
			"killnet", "lapsus", "scattered", "actor", "threat actor",
			"ransomware group", "cybercrime", "hacktivist",
		],
		"anti_keywords": [
			"the attacker", "the actor", "the adversary", "threat actors",
			"attackers", "unknown actor", "unidentified",
		],
	},
	EntityType.MALWARE: {
		"subtypes": [
			"trojan/backdoor", "ransomware", "worm", "dropper/downloader",
			"rootkit", "wiper", "spyware", "botnet client", "webshell",
			"malicious script/macro", "malicious document",
		],
		"patterns": [],
		"keywords": [
			"malware", "trojan", "backdoor", "ransomware", "worm", "rat",
			"rootkit", "wiper", "spyware", "botnet", "webshell", "loader",
			"dropper", "downloader", "stealer", "infostealer", "keylogger",
			"beacon", "implant", "payload", "exploit kit",
		],
		"anti_keywords": [
			"malicious activity", "malicious behavior", "the malware",
			"a malware", "malware family", "malware variant",
		],
	},
	EntityType.TOOL: {
		"subtypes": [
			"pentest framework", "credential tool", "remote admin tool",
			"system built-in tool", "network tool", "lateral movement tool",
			"data exfiltration tool", "persistence tool", "anti-forensics tool",
			"enumeration/scanning tool",
		],
		"patterns": [],
		"keywords": [
			"mimikatz", "psexec", "powershell", "cmd", "wmi", "certutil",
			"mshta", "rundll32", "regsvr32", "bitsadmin", "nmap", "masscan",
			"netcat", "curl", "wget", "impacket", "crackmapexec", "bloodhound",
			"rclone", "winscp", "7-zip", "megasync", "anydesk", "teamviewer",
			"cobalt strike", "brute ratel", "metasploit", "sliver",
			"lazagne", "rubeus", "kekeo", "sharphound", "adfind", "nltest",
			"process hacker", "gmer", "pchunter", "procdump",
			"schtasks", "at.exe", "sc.exe", "net.exe", "wmic",
		],
		"anti_keywords": [
			"the tool", "a tool", "tools used", "various tools",
			"legitimate tool", "open source tool",
		],
	},
	EntityType.VULNERABILITY: {
		"subtypes": [
			"CVE vulnerability", "zero-day", "RCE", "privilege escalation",
			"SQL injection", "XSS", "auth bypass", "buffer overflow",
			"deserialization", "configuration flaw",
		],
		"patterns": [
			re.compile(r"(?i)\bCVE-\d{4}-\d{4,7}\b"),
			re.compile(r"(?i)\bzero[- ]?day\b"),
			re.compile(r"(?i)\b0[- ]?day\b"),
		],
		"keywords": [
			"cve-", "vulnerability", "exploit", "rce", "remote code execution",
			"privilege escalation", "lpe", "local privilege",
			"buffer overflow", "heap overflow", "stack overflow",
			"sql injection", "sqli", "xss", "cross-site",
			"authentication bypass", "auth bypass",
			"deserialization", "path traversal", "directory traversal",
			"command injection", "code injection",
			"use-after-free", "race condition", "integer overflow",
			"eternalblue", "log4shell", "shellshock", "heartbleed",
			"printnightmare", "proxylogon", "proxyshell", "zerologon",
			"follina", "spring4shell",
		],
		"anti_keywords": [
			"the vulnerability", "a vulnerability", "vulnerabilities",
			"security flaw", "security issue", "security weakness",
		],
	},
	EntityType.ASSETS: {
		"subtypes": [
			"operating system", "server software", "database",
			"network device", "cloud platform/service", "application software",
			"middleware/framework", "virtualization platform",
			"IoT/OT device", "protocol/service",
		],
		"patterns": [
			re.compile(r"(?i)\bwindows\s+(server\s+)?\d+"),  # Windows 10, Windows Server 2019
			re.compile(r"(?i)\b(ubuntu|debian|centos|rhel|fedora)\s*\d*"),
		],
		"keywords": [
			"windows", "linux", "macos", "android", "ios", "unix",
			"apache", "nginx", "iis", "exchange server", "sharepoint",
			"mysql", "mssql", "postgresql", "mongodb", "redis", "oracle db",
			"cisco", "fortinet", "fortigate", "palo alto", "juniper",
			"aws", "azure", "gcp", "office 365", "microsoft 365",
			"adobe", "chrome", "firefox", "java", "flash",
			"struts", "spring", "log4j", "weblogic", "tomcat", "jboss",
			"vmware", "esxi", "hyper-v", "docker", "kubernetes",
			"scada", "plc", "ics", "iot",
			"smb", "rdp", "ssh", "dns", "ldap", "kerberos", "ftp",
			"active directory", "domain controller",
		],
		"anti_keywords": [
			"the system", "the server", "the application", "the network",
			"systems", "servers", "applications", "networks",
			"target system", "victim system", "affected system",
		],
	},
	EntityType.INFRASTRUCTURE: {
		"subtypes": [
			"C2 server", "malicious domain", "malicious IP",
			"phishing site", "malicious mail server", "proxy/relay",
			"download server", "exfiltration endpoint",
			"botnet infrastructure", "abused legitimate service",
		],
		"patterns": [
			re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),             # IPv4
			re.compile(r"\b(?:[a-f0-9]{0,4}:){2,7}[a-f0-9]{0,4}\b"),  # IPv6
			re.compile(r"(?i)\b[a-z0-9]([a-z0-9-]*[a-z0-9])?(\.[a-z]{2,})+\b"),  # domain
			re.compile(r"(?i)\bhttps?://\S+"),                       # URL
		],
		"keywords": [
			"c2", "c&c", "command and control", "command-and-control",
			"c2 server", "c2 infrastructure",
			"malicious domain", "malicious ip", "malicious url",
			"phishing site", "phishing page", "watering hole",
			"download server", "staging server", "relay server",
			"proxy", "vpn server", "tor", "bulletproof hosting",
			"botnet", "dead drop resolver",
			"github", "pastebin", "telegram", "discord",
		],
		"anti_keywords": [
			"the infrastructure", "the server", "infrastructure used",
			"network infrastructure", "it infrastructure",
		],
	},
	EntityType.TARGET: {
		"subtypes": [
			"industry/sector", "country/region", "organization type",
			"specific organization", "supply chain segment",
		],
		"patterns": [],
		"keywords": [
			"government", "military", "defense", "financial", "banking",
			"healthcare", "energy", "oil", "gas", "telecom",
			"education", "university", "research", "technology",
			"manufacturing", "transportation", "aviation", "maritime",
			"retail", "media", "legal", "pharmaceutical",
			"critical infrastructure", "supply chain",
			"united states", "china", "russia", "iran", "north korea",
			"south korea", "japan", "germany", "france", "uk",
			"united kingdom", "israel", "india", "brazil", "canada",
			"australia", "ukraine", "taiwan", "singapore",
			"europe", "asia", "middle east", "southeast asia",
			"nato", "embassy", "ngo", "think tank",
			"contractor", "vendor", "supplier",
		],
		"anti_keywords": [
			"the target", "the victim", "targets", "victims",
			"targeted entities", "target organizations",
		],
	},
	EntityType.EVENT: {
		"subtypes": [
			"APT campaign", "ransomware incident", "data breach",
			"DDoS attack", "supply chain attack", "espionage operation",
			"phishing campaign",
		],
		"patterns": [
			re.compile(r"(?i)\boperation\s+\w+"),            # Operation Aurora
			re.compile(r"(?i)\bcampaign\s+\w+"),             # Campaign X
		],
		"keywords": [
			"operation", "campaign", "incident", "breach", "attack",
			"intrusion", "compromise", "supply chain attack",
			"solarwinds", "kaseya", "colonial pipeline",
		],
		"anti_keywords": [
			"the event", "the incident", "the attack", "the campaign",
			"security event", "security incident", "an attack",
			"attack activity", "malicious activity",
		],
	},
	EntityType.BEHAVIOR: {
		"subtypes": [
			"reconnaissance", "resource development", "initial access",
			"execution", "persistence", "privilege escalation",
			"defense evasion", "credential access", "discovery",
			"lateral movement", "collection", "command and control",
			"exfiltration", "impact",
		],
		"patterns": [
			re.compile(r"(?i)\bT\d{4}(\.\d{3})?\b"),         # MITRE ATT&CK IDs: T1059, T1059.001
		],
		"keywords": [
			"reconnaissance", "scanning", "probing",
			"initial access", "spear phishing", "phishing", "watering hole",
			"drive-by", "exploit public-facing",
			"execution", "command-line", "scripting", "scheduled task",
			"persistence", "registry run key", "boot autostart",
			"privilege escalation", "token manipulation", "uac bypass",
			"defense evasion", "process injection", "obfuscation",
			"masquerading", "timestomping", "disabling security",
			"credential access", "credential dumping", "brute force",
			"pass-the-hash", "pass-the-ticket", "kerberoasting",
			"discovery", "network scanning", "account enumeration",
			"lateral movement", "remote services", "smb lateral",
			"collection", "screen capture", "clipboard",
			"command and control", "c2 communication", "dns tunneling",
			"encrypted channel", "data encoding",
			"exfiltration", "data exfiltration", "data staging",
			"impact", "data encryption", "data destruction",
			"defacement", "denial of service",
		],
		"anti_keywords": [
			"the behavior", "the technique", "the tactic",
			"attack behavior", "malicious behavior",
			"various techniques", "multiple techniques",
		],
	},
	EntityType.TIME: {
		"subtypes": [
			"absolute timestamp", "date range", "relative time",
			"duration", "report date",
		],
		"patterns": [
			re.compile(r"\b\d{4}[-/]\d{1,2}[-/]\d{1,2}\b"),               # 2023-05-15
			re.compile(r"(?i)\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\b"),
			re.compile(r"(?i)\bQ[1-4]\s+\d{4}\b"),                        # Q1 2024
			re.compile(r"(?i)\b(?:since|from|in|during)\s+\d{4}\b"),       # since 2015
			re.compile(r"(?i)\b\d{4}\s*[-–]\s*\d{4}\b"),                   # 2022-2024
			re.compile(r"(?i)\b(?:early|mid|late)\s+\d{4}\b"),             # early 2023
		],
		"keywords": [
			"january", "february", "march", "april", "may", "june",
			"july", "august", "september", "october", "november", "december",
			"2015", "2016", "2017", "2018", "2019", "2020",
			"2021", "2022", "2023", "2024", "2025", "2026",
		],
		"anti_keywords": [],
	},
	EntityType.CREDENTIAL: {
		"subtypes": [
			"username/password", "default credential", "API key/token",
			"digital certificate", "SSH key", "session credential",
			"Kerberos ticket", "NTLM hash",
		],
		"patterns": [],
		"keywords": [
			"credential", "password", "username", "login",
			"api key", "token", "oauth", "jwt", "session",
			"certificate", "ssh key", "private key", "public key",
			"kerberos", "tgt", "tgs", "ntlm", "hash",
			"cookie", "session id", "access token", "refresh token",
			"secret", "passphrase",
		],
		"anti_keywords": [
			"the credential", "credentials used", "stolen credentials",
			"credential access", "credential dumping",
		],
	},
	EntityType.INDICATOR: {
		"subtypes": [
			"file hash (MD5)", "file hash (SHA-1)", "file hash (SHA-256)",
			"malicious IP (IOC)", "malicious domain (IOC)", "malicious URL (IOC)",
			"email address", "file name/path", "registry key",
			"YARA rule", "mutex", "User-Agent", "JA3/JA3S fingerprint",
			"SNORT/Suricata rule",
		],
		"patterns": [
			re.compile(r"\b[a-fA-F0-9]{32}\b"),           # MD5
			re.compile(r"\b[a-fA-F0-9]{40}\b"),           # SHA-1
			re.compile(r"\b[a-fA-F0-9]{64}\b"),           # SHA-256
			re.compile(r"\b[a-fA-F0-9]{128}\b"),          # SHA-512
			re.compile(r"(?i)\brule\s+\w+\s*\{"),          # YARA rule
		],
		"keywords": [
			"hash", "md5", "sha1", "sha256", "sha-1", "sha-256",
			"ioc", "indicator of compromise",
			"file hash", "file name", "file path",
			"registry key", "registry value",
			"yara", "snort", "suricata",
			"mutex", "user-agent", "ja3",
		],
		"anti_keywords": [
			"the indicator", "indicators", "iocs found",
			"indicator of compromise", "indicators of compromise",
		],
	},
}


# ---------------------------------------------------------------------------
# Generic / abstract words that should NEVER be an entity name on their own.
# These are type-independent — any entity whose name is exactly one of these
# (case-insensitive) is rejected regardless of EntityType.
# ---------------------------------------------------------------------------

_GLOBAL_REJECT_NAMES: Set[str] = {
	# Generic computing terms (the "computer" problem)
	"computer", "computers", "machine", "machines", "device", "devices",
	"network", "networks", "internet", "data", "file", "files",
	"program", "programs", "software", "code", "script",
	"user", "users", "account", "accounts", "information",
	"system", "systems", "server", "servers", "service", "services",
	"application", "applications", "platform", "database",
	# Generic threat terms
	"attacker", "attackers", "the attacker", "the actor", "the adversary",
	"threat actor", "threat actors", "actor", "actors", "adversary",
	"hacker", "hackers", "unknown actor", "unidentified",
	"malware", "the malware", "a malware", "malware family",
	"malware variant", "malicious software",
	"tool", "the tool", "a tool", "tools", "various tools",
	"vulnerability", "the vulnerability", "a vulnerability",
	"vulnerabilities", "security flaw", "security issue",
	"target", "the target", "targets", "victim", "the victim", "victims",
	"event", "the event", "incident", "the incident",
	"attack", "the attack", "attacks", "an attack",
	"campaign", "the campaign", "activity", "malicious activity",
	"behavior", "the behavior", "technique", "the technique",
	"indicator", "the indicator", "indicators",
	"credential", "the credential", "credentials",
	"infrastructure", "the infrastructure",
	# Other overly vague terms
	"it", "they", "them", "this", "that", "these", "those",
	"entity", "entities", "object", "objects", "resource", "resources",
	"component", "components", "module", "modules", "process", "processes",
	"connection", "connections", "communication", "communications",
	"method", "methods", "approach", "operation", "operations",
}


def validate_entity_name(entity_type: EntityType, name: str) -> bool:
	"""Validate that an entity name is concrete enough for the given type.

	Strategy: PERMISSIVE by default — only reject names that are clearly
	generic or abstract. Any name that is not in the reject lists passes.

	Rejection criteria (any one triggers rejection):
	1. Name is in the global reject list (common generic words)
	2. Name is in the type-specific anti_keywords list
	3. Name is a single common English word with no specificity

	Returns True if the entity name is acceptable, False if too abstract.
	"""
	if not name or not name.strip():
		return False

	name_stripped = name.strip()
	name_lower = name_stripped.lower()

	# Rule 1: Global reject list — exact match
	if name_lower in _GLOBAL_REJECT_NAMES:
		return False

	# Rule 2: Type-specific anti_keywords — exact match
	constraints = ENTITY_SUBTYPE_CONSTRAINTS.get(entity_type)
	if constraints:
		for anti_kw in constraints.get("anti_keywords", []):
			if name_lower == anti_kw:
				return False

	# Rule 3: Single-word names that are too generic
	# (single common English words without any specificity marker)
	words = name_stripped.split()
	if len(words) == 1 and len(name_stripped) <= 15:
		# Allow if it matches a known pattern (CVE, IP, hash, etc.)
		if constraints:
			for pattern in constraints.get("patterns", []):
				if pattern.search(name_stripped):
					return True
		# Allow if it contains digits (likely a version, ID, etc.)
		if any(c.isdigit() for c in name_stripped):
			return True
		# Allow if it starts with uppercase (likely a proper noun)
		if name_stripped[0].isupper():
			return True
		# Reject single lowercase generic words
		if name_lower in {
			"access", "admin", "alert", "analysis", "api", "app",
			"binary", "bot", "browser", "bug", "cache", "call",
			"chain", "channel", "client", "cloud", "cluster",
			"command", "config", "console", "container", "control",
			"cookie", "core", "daemon", "debug", "default",
			"deploy", "desktop", "directory", "disk", "domain",
			"driver", "email", "endpoint", "engine", "entry",
			"error", "event", "exploit", "extension", "feature",
			"firewall", "firmware", "flag", "folder", "framework",
			"function", "gateway", "group", "handler", "header",
			"hook", "host", "image", "input", "instance",
			"interface", "kernel", "key", "layer", "library",
			"link", "listener", "loader", "log", "login",
			"malware", "manager", "memory", "message", "method",
			"model", "monitor", "node", "object", "output",
			"package", "packet", "page", "panel", "parser",
			"patch", "path", "payload", "permission", "pipeline",
			"plugin", "policy", "port", "portal", "printer",
			"probe", "profile", "project", "prompt", "protocol",
			"proxy", "query", "queue", "record", "registry",
			"relay", "remote", "report", "request", "response",
			"router", "rule", "runtime", "sample", "scanner",
			"schema", "screen", "sector", "segment", "sensor",
			"session", "shell", "signal", "signature", "site",
			"socket", "source", "stack", "stage", "storage",
			"stream", "string", "subnet", "switch", "table",
			"task", "template", "terminal", "thread", "ticket",
			"token", "traffic", "trigger", "tunnel", "update",
			"upload", "utility", "value", "vector", "version",
			"volume", "webhook", "worker", "wrapper", "zone",
		}:
			return False

	# Everything else passes — be permissive
	return True


# ---------------------------------------------------------------------------
# Valid source->target type constraints for relations.
# Each relation maps to a LIST of valid (source_type, target_type) pairs.
# ---------------------------------------------------------------------------

RELATION_TYPE_CONSTRAINTS: Dict[RelationType, List[Tuple[EntityType, EntityType]]] = {
	RelationType.HAS: [
		(EntityType.ATTACKER, EntityType.MALWARE),       # APT28 has Zebrocy
		(EntityType.ATTACKER, EntityType.CREDENTIAL),    # APT持有被盗凭证
		(EntityType.ATTACKER, EntityType.INDICATOR),     # APT关联的IOC
		(EntityType.MALWARE, EntityType.INDICATOR),      # 恶意软件的hash/签名
		(EntityType.MALWARE, EntityType.BEHAVIOR),       # 恶意软件的TTP特征
		(EntityType.INFRASTRUCTURE, EntityType.INDICATOR),  # C2的域名/IP指标
		(EntityType.EVENT, EntityType.TIME),             # 事件发生时间
		(EntityType.EVENT, EntityType.INDICATOR),        # 事件关联IOC
	],
	RelationType.USES: [
		(EntityType.ATTACKER, EntityType.TOOL),          # APT28 uses Mimikatz
		(EntityType.ATTACKER, EntityType.CREDENTIAL),    # 攻击者使用凭证
		(EntityType.MALWARE, EntityType.TOOL),           # 恶意软件调用合法工具
		(EntityType.MALWARE, EntityType.INFRASTRUCTURE), # 恶意软件连接C2
		(EntityType.EVENT, EntityType.TOOL),             # 事件中使用的工具
	],
	RelationType.EXPLOIT: [
		(EntityType.MALWARE, EntityType.VULNERABILITY),  # SUNBURST exploits CVE-X
		(EntityType.ATTACKER, EntityType.VULNERABILITY), # 攻击者直接利用漏洞
		(EntityType.TOOL, EntityType.VULNERABILITY),     # 工具利用漏洞
	],
	RelationType.EXIST: [
		(EntityType.VULNERABILITY, EntityType.ASSETS),   # CVE-X exists in Log4j
		(EntityType.MALWARE, EntityType.ASSETS),         # 恶意软件存在于资产
		(EntityType.INDICATOR, EntityType.ASSETS),       # IOC出现在资产中
	],
	RelationType.TARGET: [
		(EntityType.ATTACKER, EntityType.TARGET),        # APT29 targets government
		(EntityType.MALWARE, EntityType.TARGET),         # 恶意软件针对的目标
		(EntityType.EVENT, EntityType.TARGET),           # 事件针对的目标
		(EntityType.ATTACKER, EntityType.ASSETS),        # 攻击者瞄准的资产
		(EntityType.MALWARE, EntityType.ASSETS),         # 恶意软件针对的系统
	],
	RelationType.MEDIUM: [
		(EntityType.ATTACKER, EntityType.INFRASTRUCTURE),  # 攻击者以基础设施为媒介
		(EntityType.MALWARE, EntityType.INFRASTRUCTURE),   # 恶意软件通过基础设施通信
		(EntityType.EVENT, EntityType.INFRASTRUCTURE),     # 事件涉及的基础设施
	],
	RelationType.BEHAVIOR: [
		(EntityType.EVENT, EntityType.BEHAVIOR),         # 事件表现出某行为
		(EntityType.ATTACKER, EntityType.BEHAVIOR),      # 攻击者采用某TTP
		(EntityType.MALWARE, EntityType.BEHAVIOR),       # 恶意软件的行为
		(EntityType.TOOL, EntityType.BEHAVIOR),          # 工具关联的行为
	],
}


def validate_relation_types(
	relation_type: RelationType,
	source_type: EntityType,
	target_type: EntityType,
) -> bool:
	"""Check if a relation's source/target entity types satisfy the constraints."""
	allowed_pairs = RELATION_TYPE_CONSTRAINTS.get(relation_type, [])
	return (source_type, target_type) in allowed_pairs


class CSKGEntity(BaseModel):
	"""CSKG4APT Entity"""

	id: str = Field(..., min_length=1, description="Unique entity identifier")
	type: EntityType = Field(..., description="Entity type from 12 CSKG4APT types")
	name: str = Field(..., min_length=1, description="Entity name")
	aliases: List[str] = Field(default_factory=list, description="Alternative names")
	derivation_source: str = Field(..., min_length=1, description="Source text evidence")
	confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Extraction confidence")
	attributes: Optional[Dict] = Field(default=None, description="Additional attributes")

	@field_validator("type", mode="before")
	@classmethod
	def coerce_entity_type(cls, v):
		if isinstance(v, str):
			# Try exact match first
			for member in EntityType:
				if v == member.value or v.lower() == member.value.lower():
					return member
			# Try enum name match
			try:
				return EntityType[v.upper()]
			except KeyError:
				pass
		return v

	@field_validator("confidence", mode="before")
	@classmethod
	def clamp_confidence(cls, v):
		if isinstance(v, (int, float)):
			return max(0.0, min(1.0, float(v)))
		return v

	@model_validator(mode="after")
	def check_entity_specificity(self):
		"""Validate that the entity name is concrete enough for its type.

		Abstract/generic names (e.g. 'the attacker', 'the malware') get their
		confidence penalised so they are deprioritised or filtered downstream.
		"""
		if not validate_entity_name(self.type, self.name):
			logger.warning(
				"Entity '%s' (type=%s) rejected by subtype constraints — "
				"name is too abstract or generic",
				self.name,
				self.type.value,
			)
			self.confidence = 0.0
		return self


class CSKGRelation(BaseModel):
	"""CSKG4APT Relation"""

	source_entity_id: str = Field(..., min_length=1, description="Source entity ID")
	target_entity_id: str = Field(..., min_length=1, description="Target entity ID")
	relation_type: RelationType = Field(..., description="Relation type from 7 CSKG4APT types")
	derivation_source: str = Field(..., min_length=1, description="Source text evidence")
	confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Extraction confidence")

	@field_validator("relation_type", mode="before")
	@classmethod
	def coerce_relation_type(cls, v):
		if isinstance(v, str):
			for member in RelationType:
				if v == member.value or v.lower() == member.value.lower():
					return member
			try:
				return RelationType[v.upper()]
			except KeyError:
				pass
		return v

	@field_validator("confidence", mode="before")
	@classmethod
	def clamp_confidence(cls, v):
		if isinstance(v, (int, float)):
			return max(0.0, min(1.0, float(v)))
		return v


class CSKG4APTGraph(BaseModel):
	"""CSKG4APT Knowledge Graph container"""

	name: str = Field(default_factory=lambda: f"CSKG4APT-{int(time.time())}")
	source_url: Optional[str] = None
	source_text: str = Field(..., description="Original CTI text")
	extraction_timestamp: str = Field(
		default_factory=lambda: time.strftime("%Y-%m-%d %H:%M:%S")
	)
	entities: List[CSKGEntity] = Field(default_factory=list)
	relations: List[CSKGRelation] = Field(default_factory=list)
	metadata: Dict = Field(default_factory=dict)

	def get_entity(self, entity_id: str) -> Optional[CSKGEntity]:
		"""Get entity by ID"""
		for entity in self.entities:
			if entity.id == entity_id:
				return entity
		return None

	def get_entities_by_type(self, entity_type: EntityType) -> List[CSKGEntity]:
		"""Get all entities of a given type"""
		return [e for e in self.entities if e.type == entity_type]

	def get_outgoing_relations(self, entity_id: str) -> List[CSKGRelation]:
		"""Get all relations where entity_id is the source"""
		return [r for r in self.relations if r.source_entity_id == entity_id]

	def get_incoming_relations(self, entity_id: str) -> List[CSKGRelation]:
		"""Get all relations where entity_id is the target"""
		return [r for r in self.relations if r.target_entity_id == entity_id]

	def to_networkx(self):
		"""Convert to NetworkX directed graph"""
		import networkx as nx

		G = nx.DiGraph()
		for entity in self.entities:
			G.add_node(
				entity.id,
				type=entity.type.value,
				name=entity.name,
				confidence=entity.confidence,
			)
		for relation in self.relations:
			G.add_edge(
				relation.source_entity_id,
				relation.target_entity_id,
				relation=relation.relation_type.value,
				confidence=relation.confidence,
			)
		return G

	def to_dict(self) -> dict:
		"""Serialize to dictionary"""
		return self.model_dump(mode="json")

	def summary(self) -> str:
		"""Generate a brief summary of the graph"""
		type_counts = {}
		for entity in self.entities:
			type_name = entity.type.value
			type_counts[type_name] = type_counts.get(type_name, 0) + 1
		rel_counts = {}
		for relation in self.relations:
			rel_name = relation.relation_type.value
			rel_counts[rel_name] = rel_counts.get(rel_name, 0) + 1
		return (
			f"CSKG4APTGraph '{self.name}': "
			f"{len(self.entities)} entities ({type_counts}), "
			f"{len(self.relations)} relations ({rel_counts})"
		)
