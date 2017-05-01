sudo mkdir -p /var/lib/postgresql/data
sudo chown vagrant:vagrant /var/lib/postgresql/data
# export the three env vars for local dev environment
echo -e "\nexport DB_NAME=${DB_NAME}\nexport DB_USER=${DB_USER}\nexport DB_PASSWORD=${DB_PASSWORD}" >> /home/vagrant/.profile
