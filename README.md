# What it does

Poll a [Yiimp pool] block found result page (usually on /site/found\_results) and post a message to [Discord] chat room.
It also feature a currency conversion to add blocks value in BTC and USDT (USD parity) using [stock.exchange] and [Cryptopia] markets API.

Single file app all written in Python 3 asyncio, it should be very easy to modify to use additionnal markets API and or different endpoints.


# System service installation

1. Install depencencies (Python 3.5+)
```
sudo apt install python3-aiohttp python3-bs4 python3-html5lib
```

2. Install script
```
sudo wget https://raw.githubusercontent.com/eLvErDe/yiimp-blocks-found-to-discord/master/yiimp-blocks-found-to-discord.py -O /usr/local/bin/yiimp-blocks-found-to-discord.py
sudo chmod 0755 /usr/local/bin/yiimp-blocks-found-to-discord.py
```

3. Register as a systemd service
```
sudo wget https://raw.githubusercontent.com/eLvErDe/yiimp-blocks-found-to-discord/master/systemd/service -O /etc/systemd/system/yiimp-blocks-found-to-discord.service 
sudo wget https://raw.githubusercontent.com/eLvErDe/yiimp-blocks-found-to-discord/master/systemd/default -O /etc/default/yiimp-blocks-found-to-discord
sudo systemctl daemon-reload
```

4. Edit `/etc/default/yiimp-blocks-found-to-discord` to set the correct pool URL and Discord web hook URL

Add `?algo=all` to the found pool URL after patching YIIMP, see information below, for example:
https://pool.ionik.fr/site/found_results?algo=all

5. Mark as autostart and start it
```
sudo systemctl enable yiimp-blocks-found-to-discord
sudo systemctl start yiimp-blocks-found-to-discord
```

6. Check application logs
```
sudo tail -n 50 -f /var/log/syslog | grep yiimp-blocks-found-to-discord
```

[Yiimp pool]: https://github.com/tpruvot/yiimp
[Discord]: https://discordapp.com/
[stock.exchange]: https://stocks.exchange/
[Cryptopia]: https://www.cryptopia.co.nz/

# Old aiohttp version

```
[poll_yiimp_events        ] Exception occurred: AttributeError: __aexit__
Traceback (most recent call last):
File "/usr/local/bin/yiimp-blocks-found-to-discord.py", line 109, in poll_yiimp_events
    async with aiohttp.ClientSession() as session:
AttributeError: __aexit__
```

If you see theses errors, you are using and old python3-aiohttp which is not compatible with current version.
Please get the file from the [old-aiohttp-compat-branch] instead.

[old-aiohttp-compat-branch]: https://github.com/eLvErDe/yiimp-blocks-found-to-discord/tree/old-aiohttp-compat

# Patching YIIMP code to provide statistics for all algorithms

You will need a very small patch on your YIIMP installation: https://github.com/tpruvot/yiimp/pull/256/files

To make thing easier, I suggest you just overwrite found_results.php file with the one from here: https://raw.githubusercontent.com/eLvErDe/yiimp/found-results-algo-filter-as-query-param/web/yaamp/modules/site/results/found_results.php
