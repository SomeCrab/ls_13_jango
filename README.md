
```bash
cd deploy/ && docker-compose down && cd .. && docker system prune -a && docker volume rm deploy_pgdata && docker-compose -f deploy/docker-compose.yml up postgres --build --force-recreate -d && docker-compose -f deploy/docker-compose.yml up migration --build --force-recreate -d && docker-compose -f deploy/docker-compose.yml up app1 --build --force-recreate -d && docker-compose -f deploy/docker-compose.yml up app2 --build --force-recreate -d && docker-compose -f deploy/docker-compose.yml up nginx --build --force-recreate -d
```

```bash
docker-compose run app1 sh -c "python manage.py migrate && echo 'Migrations ran'"
```

# clean
```bash
cd deploy/ && docker-compose down && cd .. && docker system prune -a && docker volume rm deploy_pgdata 
```

# run basic variant locally show - no migrations
```bash
docker-compose -f deploy/docker-compose.yml up postgres --build --force-recreate -d
docker-compose -f deploy/docker-compose.yml up app1 --build --force-recreate -d
```

# run basic variant in container (app1 + postgres) + manual migration
```bash
docker-compose run app1 sh -c "python manage.py migrate && echo 'Migrations ran'"
```

# run basic variant in container (app1 + postgres) + container migration
```bash
cd deploy/ && docker-compose down && cd .. && docker system prune -a && docker volume rm deploy_pgdata 
docker-compose -f deploy/docker-compose.yml up postgres --build --force-recreate -d
docker-compose -f deploy/docker-compose.yml up migration --build --force-recreate -d
docker-compose -f deploy/docker-compose.yml up app1 --build --force-recreate -d
```

# run 2 instances show them
```bash
docker-compose -f deploy/docker-compose.yml up app2 --build --force-recreate -d
```

# add nginx - balancer
```bash
docker-compose -f deploy/docker-compose.yml up nginx --build --force-recreate -d
```

```bash
npx loadtest -c 1000 --rps 200 http://localhost:8000
npx loadtest -c 1000 --rps 200 http://localhost:80
```