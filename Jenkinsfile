pipeline {

    // ── AGENT ────────────────────────────────────────────────────────────────
    // agent any  →  run on Jenkins master container itself
    // Since our Jenkins container has Docker socket mounted, it CAN run docker
    // commands directly. We use agent any + sh 'docker ...' for simplicity.
    agent any

    // ── PARAMETERS ───────────────────────────────────────────────────────────
    parameters {
        string(
            name: 'DOCKER_IMAGE_NAME',
            defaultValue: 'todo-app',
            description: 'Docker image name (without registry prefix)'
        )
        choice(
            name: 'ENVIRONMENT',
            choices: ['dev', 'staging', 'prod'],
            description: 'Target deployment environment'
        )
        booleanParam(
            name: 'PUSH_TO_DOCKERHUB',
            defaultValue: true,
            description: 'Push image to DockerHub after build?'
        )
    }

    // ── ENVIRONMENT VARIABLES ────────────────────────────────────────────────
    environment {
        // Static values
        APP_PORT        = '5000'
        SONAR_HOST_URL  = 'http://local-sonar:9000'   // sonarqube container name = hostname inside Docker network

        // Computed from built-in Jenkins vars + params
        IMAGE_TAG       = "${params.DOCKER_IMAGE_NAME}:${env.BUILD_NUMBER}"
        IMAGE_LATEST    = "${params.DOCKER_IMAGE_NAME}:latest"

        // --- Credentials (set these in Jenkins UI first) ---
        // Jenkins UI → Manage Jenkins → Credentials → Global
        // ID: dockerhub-creds  → Username/Password → your DockerHub login
        // ID: sonar-token      → Secret Text       → your SonarQube token
        DOCKERHUB_CREDS = credentials('dockerhub-creds')
        // ^ creates two vars automatically:
        //   DOCKERHUB_CREDS_USR  = your DockerHub username
        //   DOCKERHUB_CREDS_PSW  = your DockerHub password

        SONAR_TOKEN     = credentials('sonar-token')

        // Full image name with registry user prefix
        FULL_IMAGE      = "${DOCKERHUB_CREDS_USR}/${IMAGE_TAG}"
        FULL_LATEST     = "${DOCKERHUB_CREDS_USR}/${IMAGE_LATEST}"
    }

    // ── OPTIONS ──────────────────────────────────────────────────────────────
    options {
        timeout(time: 20, unit: 'MINUTES')
        buildDiscarder(logRotator(numToKeepStr: '5'))
        disableConcurrentBuilds()
        timestamps()
    }

    // ── STAGES ───────────────────────────────────────────────────────────────
    stages {

        stage('Checkout') {
            steps {
                echo "=== Checking out branch: ${env.GIT_BRANCH} ==="
                // 'checkout scm' uses the SCM config from the pipeline job itself
                // (the repo URL and branch you set when creating the job in Jenkins UI)
                checkout scm
                echo "Commit: ${env.GIT_COMMIT}"
            }
        }

        stage('Install Dependencies') {
            steps {
                echo "=== Installing Python dependencies ==="
                sh '''
                    python3 -m venv venv
                    . venv/bin/activate
                    pip install --upgrade pip -q
                    pip install -r requirements.txt -q
                '''
            }
        }

        stage('Run Tests') {
            steps {
                echo "=== Running tests with coverage ==="
                sh '''
                    . venv/bin/activate
                    pytest -v \
                      --cov=app \
                      --cov-report=xml:coverage.xml \
                      --cov-report=term-missing \
                      --junitxml=test-results.xml
                '''
            }
            post {
                always {
                    // Publish JUnit test results in Jenkins UI
                    junit 'test-results.xml'
                }
            }
        }

        stage('SonarQube Analysis') {
            steps {
                echo "=== Running SonarQube analysis ==="
                sh """
                    . venv/bin/activate
                    pip install coverage -q
                    sonar-scanner \
                      -Dsonar.projectKey=todo-app \
                      -Dsonar.sources=. \
                      -Dsonar.python.coverage.reportPaths=coverage.xml \
                      -Dsonar.host.url=${SONAR_HOST_URL} \
                      -Dsonar.token=${SONAR_TOKEN} \
                      -Dsonar.exclusions=venv/**,tests/**
                """
            }
        }

        stage('Docker Build') {
            steps {
                echo "=== Building Docker image: ${FULL_IMAGE} ==="
                sh "docker build -t ${FULL_IMAGE} -t ${FULL_LATEST} ."
            }
        }

        stage('Docker Push') {
            when {
                // Only push if param says so
                expression { return params.PUSH_TO_DOCKERHUB }
            }
            steps {
                echo "=== Pushing to DockerHub as ${DOCKERHUB_CREDS_USR} ==="
                sh """
                    echo ${DOCKERHUB_CREDS_PSW} | docker login -u ${DOCKERHUB_CREDS_USR} --password-stdin
                    docker push ${FULL_IMAGE}
                    docker push ${FULL_LATEST}
                    docker logout
                """
            }
        }

        stage('Verify Running Container') {
            steps {
                echo "=== Smoke test — run container and hit /todos ==="
                sh """
                    docker run -d --name todo-smoke-test -p 5001:5000 ${FULL_IMAGE}
                    sleep 3
                    curl -f http://localhost:5001/todos || (docker rm -f todo-smoke-test && exit 1)
                    docker rm -f todo-smoke-test
                """
            }
        }
    }

    // ── POST ─────────────────────────────────────────────────────────────────
    post {
        always {
            echo "=== Cleaning workspace ==="
            sh 'rm -rf venv __pycache__ .pytest_cache'
            cleanWs()
        }
        success {
            echo "✅ Pipeline passed! Image: ${FULL_IMAGE} — Environment: ${params.ENVIRONMENT}"
        }
        failure {
            echo "❌ Pipeline FAILED at stage. Check logs above."
            // Add slackSend or emailext here when you have those plugins
        }
    }
}
