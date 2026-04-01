build:
docker buildx build \
  --platform linux/amd64 \
  -t lalghisi/dbrecover:2.0.0 \
  -t lalghisi/dbrecover:latest \
  --push \
  -f Dockerfile \
  .


build:
docker buildx build \
  --platform linux/amd64 \
  -t lalghisi/dbrecover-staging:2.0.0 \
  -t lalghisi/dbrecover-staging:latest \
  --push \
  -f Dockerfile \
  .