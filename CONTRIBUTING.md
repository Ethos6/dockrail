# Contributing

Thanks for considering a contribution. Keep changes small and focused, include a test for behavior changes, and avoid adding runtime dependencies unless there is a strong reason.

Before opening a pull request:

```sh
python -m unittest discover -s tests -v
python -m compileall -q dockrail tests
git diff --check
```

Do not include passwords, private keys, `.env` files, or live server details in issues, commits, or tests. Remote end-to-end tests must use disposable infrastructure and must not run in the default test suite.
