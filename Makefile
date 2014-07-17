
SCRIPT	  :=  ./artifact-manager


TRANSPORT := http basew local smb
LIBS	  := __init__ $(TRANSPORT:%=transport/%) reader manager
LIBFILES  := $(LIBS:%=lib/artmgr/%.py)
MAIN      := artifact-manager.py


all: standalone

standalone:	$(SCRIPT)

unit: $(SCRIPT)
	./artifact-manager-wrapper --exec test

clean:
	rm $(SCRIPT) $(SCRIPT)c

$(SCRIPT): $(LIBFILES) $(MAIN)
	@echo "merging files into $(SCRIPT)"
	@( sed -e '1, /<====/ ! d'    $(MAIN); \
	   sed -e '/<====/,/====>/ d' $(LIBFILES); \
	   sed -e '1,/====>/ d'       $(MAIN) ) > $@
