wheel: clean
	python setup.py build bdist_wheel

pex:
	pip freeze > pip_freeze.txt
	pex -o singtclient.pex -e singtclient:go  -r pip_freeze.txt

clean:
	rm -f singt.pex
	rm -f pip_freeze.txt
	rm -rf dist

cloc:
	cloc --exclude-list-file=exclude-list.txt singtclient
