# IPADown
Web frontend for [ipatool-py](https://github.com/nyaMisty/ipatool-py/)

## Features
* Can downgrade iOS apps
* Works jailed, on the latest iOS version

## How to setup
1. Follow the guide on how to setup iTunes for older app versions in the ipatool-py repo.
2. Generate some self-signed ssl certs or get legit ones and copy them to the "ssl" folder.
   * ssl/private.key && ssl/public.crt
3. Fill in config.json, using the example at config.json.example.
4. Run the main.py, and visit the webpage at your ip

## Disclaimer
This script was supposed to be just a private thing, not meant for the public to see. After showing it to some people, they requested for it to be publicised. The code quality is shit, and I know that, because it was supposed to be only by me.
There's probably lots of vulnerabilities in this, which is why I don't recommend hosting a public instance, but it works fine for local use.
