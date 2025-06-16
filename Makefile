build:
	docker buildx build -t lalghisi/dbrecover --platform linux/amd64 --push . -f Dockerfile
