FROM ghcr.io/goccy/bigquery-emulator:0.6.5

ENTRYPOINT [ "/bin/bigquery-emulator", "--dataset", "test-dataset", "--project", "test-project" ]
