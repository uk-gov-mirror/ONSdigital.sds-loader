# sds-loader

![Version](https://ons-badges-752336435892.europe-west2.run.app/api/badge/custom?left=Python&right=3.13)

A microservice for loading and modifying data into SDS


### Install dependencies

This command will install all the dependencies required for the project, including development dependencies:

```
uv sync
```

If you ever need to update the dependencies, you can run:

```bash
uv sync --upgrade
```

## Generate `.env`

To use environment variables, you need to create a `.env` file in the root directory of the project. You can copy the `.env.example` file and rename it to `.env`:

```bash
cp .env.example .env
```

## Running the service

```bash
make dev
```

## Linting

```bash
make lint
```

## Formatting

```bash
make format
```

## Tests

```bash
make test
```

## OpenApi spec

[http://0.0.0.0:5000/docs](http://0.0.0.0:5000/docs)

## Dockerize

```
docker build -t sds-loader .
```

## Profiles

sds-loader uses "profiles" to determine the concrete implementation of the abstracted services it uses.

For example when running locally, you may just want to use fake repositories and test the business logic of the application, whereas in production you will want to use a Firestore database, GCP etc.

Profiles are determined by the `PROFILE` environment variable. This will default to `prod` if not set. The following profiles are available...

- `prod`: This profile will use the real implementations of all services. This is the default profile.
- `dev`: This profile will use fake repositories and services that do not connect to any real services
- `local_storage_firestore` This will use fake repositories for all services except the `DatasetStorageRepositoryInterface` which will use Firestore. To set up a local Firestore read the instructions below...

## Firestore emulator

In order to use Firestore locally, you will need to set up the Firestore emulator. You can do this using Docker. Run the following command to start the Firestore emulator:

You will need to set the environment variable FIRESTORE_EMULATOR_HOST to instruct the application to connect to the emulator instead of the real Firestore service...

```bash
export FIRESTORE_EMULATOR_HOST=localhost:8080
```

Ensure the profile for the application is set to `local_storage_firestore` to use the Firestore emulator...

```bash
export PROFILE=local_storage_firestore

# Or add it to the .env file

PROFILE=local_storage_firestore
```

Then run the following command to start the Firestore emulator in Docker. Note it takes a few seconds to start up, so you may want to run this command before starting the application...

```
docker run \
		--rm \
		-p=9000:9000 \
		-p=8080:8080 \
		-p=4000:4000 \
		-p=9099:9099 \
		-p=8085:8085 \
		-p=5001:5001 \
		-p=9199:9199 \
		--env "GCP_PROJECT=${PROJECT_ID}" \
		--env "ENABLE_UI=true" \
		spine3/firebase-emulator &
```

## Performance testing

The directory `performance_tests` contains a script for generating large datasets, that can be used to performance test the application

