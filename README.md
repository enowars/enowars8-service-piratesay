# Piratesay

Piratesay is a play on “The Pirate Bay” and mimics a dark web internet forum where users can brag about scams they have completed. The service behaves like a CLI with a pirate-theme, where users can navigate through pirate-themed locations (directories). The service is written in C and players connect through a TCP connection.

Piratesay was played as a binary service in Enowars 8 on the 20th of July 2024.

## Get Running

1. Clone the repo and run docker compose up for the both service and checker (use the local compose for the checker)

   **NOTE: The binary is compiled for x86-architecture. Should you be using something else (ARM), please navigate to the service_source folder instead and docker compose from there. This should trigger a recompilation in that folder.**

- `cd service && docker compose up --build`
- `cd checker && docker compose -f docker-compose-local.yaml up --build`

2. Connect using the connector.py script for QoL features or alternatively directly using `nc localhost 4444`

## Vulns, exploits and patches

For an in-depth look at vulns, exploits and patches, please look at the README.md in the documentation folder.

In this folder, you will also find bambixploits implementing the exploits in practice, as well as patched and unpatched stripped binaries.
