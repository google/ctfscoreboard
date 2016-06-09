# Makefile to minimize JS using UglifyJS (https://github.com/mishoo/UglifyJS2)
# or 'cat' to just assemble into one file.

MIN_JS:=static/js/app.min.js
JS_SRC:=$(shell find static/js \! -name '*.min.*' -name '*.js')
MINIFY:=$(shell which uglifyjs >/dev/null && echo `which uglifyjs` || echo cat)

# Declarations for SCSS
SCSS_SRC:=$(shell find static/scss -name '*.scss')
PYSCSS:=$(shell which pyscss >/dev/null && echo `which pyscss` || echo cat)

$(MIN_JS): $(JS_SRC)
	$(MINIFY) $^ > $@

scss: $(SCSS_SRC)
	for i in $(ls static/scss/); do $(PYSCSS) -o static/css/${i%.scss}.css static/scss/$i; done
