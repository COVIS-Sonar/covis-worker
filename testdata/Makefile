help:
	@echo "make download 			Downloads all of the COVIS test data.  Requires wget"

TEST_FILES = 2019/10/24/COVIS-20191024T003346-diffuse3.tar.gz \
							2019/10/24/COVIS-20191024T000002-imaging1.tar.gz \
							2019/10/24/COVIS-20191024T003346-diffuse3.7z \
							2019/10/24/COVIS-20191024T000002-imaging1.7z


download: $(TEST_FILES)

%.tar.gz:
	mkdir -p covis-raw/$(dir $@)
	cd covis-raw/$(dir $@) && wget https://covis-raw.s3.wasabisys.com/$@

## Since the 7z files aren't available on the public internet,
## make them locally instead.
## Computationally expensive
%.7z: %.tar.gz
	mkdir -p covis-raw/$(dir $@)
	$(eval TMP := $(shell mktemp -d))
	cd $(TMP) && tar xzvf $(abspath covis-raw/$^) | xargs 7z a $(abspath covis-raw/$@)
	rm -rf $(TMP)


.phony:  help download
