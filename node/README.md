## NetEaseCloudMusic-XiaoAi (Node.js Service)

1. Install requirements

``` bash
npm install
```

2. Create configuration file

Rename `config.json.template` to `config.json`, and then edit this file.

| Field   |      Value      |
|----------|:-------------:|
| self_url | The exposed url to access this service (include port) |
| port | The port you want to use to start this service |
| api_url | The URL of NetEase Cloud Music API service |
| username | The username of your NetEase Cloud Music account |
| password | The password of your NetEase Cloud Music account |

``` JSON
{
    "self_url": "http://YOUR_DOMAIN:PORT",
    "port": 3001,
    "api_url": "http://API_HOST:API_PORT",
    "username": "USERNAME_HERE",
    "password": "PASSWORD_HERE"
}
```


3. Run `server.js`

``` bash
node server.js
```
