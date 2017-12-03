PYTHON_MODULES := pa2human router tg

run:
	./run.sh --config niege.yml

niege lexi malena:
	-./main.py --config $@.yml

update: $(addprefix UPDATE_, $(PYTHON_MODULES)) UPDATE_core

UPDATE_core:
	@echo updating core
	.env/bin/pip3 install -U -r requirements.txt

UPDATE_%:
	@echo updating $*
	cd $*; .env/bin/pip3 install -U -r requirements.txt
