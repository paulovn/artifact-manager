# Build the standalone artifact-manager script
#
#  make all   -> builds the simple script (artifact-manager.py) and the
#		 standalone script (artifact-manager)
#  make clean -> cleans all generated files
#  make unit  -> perform unit tests
#

SCRIPT	  :=  ./artifact-manager


TRANSPORT := http basew local smb
LIBS	  := __init__ $(TRANSPORT:%=transport/%) reader manager
LIBFILES  := $(LIBS:%=lib/artmgr/%.py)
MAIN      := artifact-manager.py

# ---------------------------------------------------------------------

all: standalone

standalone:	$(SCRIPT)

unit: $(SCRIPT)
	./artifact-manager-wrapper --exec test

clean:
	rm -f $(MAIN) $(SCRIPT) $(SCRIPT)c

version:
	git rev-list develop | wc -l

# ---------------------------------------------------------------------

$(MAIN):	$(MAIN).in
	@echo ".. Inserting git release number into script version"
	@git fetch origin develop
	VERSION=$$(git rev-list develop | wc -l);  sed -e "s/\(APP_VERSION =.*\)'/\1.$${VERSION}'/" $< > $@
	chmod +x $@

$(SCRIPT): $(LIBFILES) $(MAIN)
	@echo ".. Merging files into $(SCRIPT)"
	@( sed -e '1, /<====/ ! d'    $(MAIN); \
	   sed -e '/<====/,/====>/ d' $(LIBFILES); \
	   sed -e '1,/====>/ d'       $(MAIN) ) > $@
	chmod +x $@
