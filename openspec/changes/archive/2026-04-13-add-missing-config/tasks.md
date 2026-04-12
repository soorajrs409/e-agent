## 1. Config Updates

- [x] 1.1 Add tools.call_api.timeout, tools.nmap.timeout, tools.nuclei.timeout to config.yaml
- [x] 1.2 Add logging.rotation_days, logging.backup_count to config.yaml
- [x] 1.3 Add new config to config.yaml.example

## 2. Config Loader

- [x] 2.1 Load tool timeouts in config.py
- [x] 2.2 Load logging settings in config.py

## 3. Tool Integration

- [x] 3.1 Update call_api to use call_api.timeout
- [x] 3.2 Update run_nmap to use nmap.timeout
- [x] 3.3 Update run_nuclei to use nuclei.timeout

## 4. Main Integration

- [x] 4.1 Update main.py logging to use rotation_days and backup_count from config

## 5. Verification

- [x] 5.1 Run tests
- [x] 5.2 Run lint
- [x] 5.3 Manual verification of config loading