# smart_local_networks_demo
demostrator for Smart Local Network proyect

# OS installation

You can use the [Raspberry Pi Imager](https://www.raspberrypi.com/software/) to flash the last 64-bit Bullseye ligth version (no desktop)

# Initial setup

Use raspi-config to configure the RPI

```bash
sudo raspi-config
```

- Configure the SSH interface

## Update OS

```bash
sudo apt update
sudo apt upgrade
```

## Install and configure git

```bash
sudo apt install git
git config --global user.name "Nicolas44Hernandez"
git config --global user.email n44hernandezp@gmail.com
```
## Clone repository

```bash
mkdir workspace
git clone https://github.com/Nicolas44Hernandez/smart_local_networks_demo.git
```

## Install the dependencies
```bash
cd smart_local_networks_demo
pip install -r requirements.txt
```

To add the dependencies to PATH, edit the `bashrc` file

```bash
nano ~/.bashrc
```
add line
```
export PATH="$PATH:/home/pi/.local/bin"
```

# Run the application

## Environment variables

To launch the application you must define the environment variables:

```bash
export FLASK_APP="server/app:create_app()"
export FLASK_ENV=production
```

## Create logfiles

Log files defined in configuration file located in *server/config/logging-config.yml* must be created before launching the application

```bash
mkdir logs
touch logs/app.log logs/api-rest.log logs/wifi_bands.log
```

Pour lancer l'application flask, depuis smart_local_netwoks_demo

```bash
flask run
```

## Set the application as a service

Copy the service file

```bash
sudo cp service/sln.service /etc/systemd/system/
```

Register service

```bash
sudo systemctl daemon-reload
sudo systemctl enable sln
sudo systemctl restart sln
```

## TODO
- [ ] APP
- [ ] Logs
- [ ] Service

