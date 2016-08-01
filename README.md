# jpy_rate_monitor

日幣匯率 bot

### Requirement

```shell 
pip install -r requirements.txt
```



### Config file example

`slack.conf`

```
[global]
slack_webhook_url = https://hooks.slack.com/services/T12345678/123456789/974bcurotwpconuiopnc
```

### Run

```shell
./jpy_rate_monitor.py --config slack.conf
```

or

```shell
./jpy_rate_monitor.py -c slack.conf
```

