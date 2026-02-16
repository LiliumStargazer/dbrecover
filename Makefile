build:
	docker buildx build -t lalghisi/dbrecover-staging --platform linux/amd64 --push . -f Dockerfile
