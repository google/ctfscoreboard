# Makefile to minimize JS using UglifyJS (https://github.com/mishoo/UglifyJS2)
# or 'cat' to just assemble into one file.

MIN_JS:=static/js/app.min.js
JS_SRC:=$(shell find static/js \! -name '*.min.*' -name '*.js')
MINIFY:=$(shell which uglifyjs >/dev/null && echo `which uglifyjs` || echo cat)

$(MIN_JS): $(JS_SRC)
	$(MINIFY) $^ > $@
