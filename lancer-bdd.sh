#!/bin/bash
docker run \
  --name bdd \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=mini_projet_de \
  -p 5432:5432 \
  -v $(pwd)/ddl:/docker-entrypoint-initdb.d \
  -d postgres:14.24-trixie
