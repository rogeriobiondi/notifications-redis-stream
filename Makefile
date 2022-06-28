include .env
export $(shell sed 's/=.*//' .env)

clear:
	@printf "Limpando arquivos temporários... "
	@rm -f dist/*.gz
	@rm -rfd *.egg-info
	@find . -type f -name '*.pyc' -delete
	@find . -type f -name '*.log' -delete
	@echo "OK"

install:
	@printf "Instalando bibliotecas... "
	@pip install -q --no-cache-dir -r requirements.txt
	@echo "OK"

start:
	@docker-compose up -d

consumer:
	python consumer.py

