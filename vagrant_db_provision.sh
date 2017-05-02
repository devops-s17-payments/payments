# Add DB connect string as environment variable
EXISTS=`grep LOCAL_DB /home/vagrant/.profile | wc -l | awk '{ print $1 }'`
if [[ $EXISTS -eq 0 ]]; then
  STR="\nexport LOCAL_DB=postgresql://${DB_USER}:${DB_PASSWORD}@localhost:5432/${DB_NAME}"
  echo -e $STR >> /home/vagrant/.profile
  echo "Adding DB connection string..."
else
  echo "LOCAL_DB exists!"
fi

sudo mkdir -p /var/lib/postgresql/data
sudo chown vagrant:vagrant /var/lib/postgresql/data
