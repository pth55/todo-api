pipeline {

    agent any

    parameters {
        string(name: 'IMAGE_NAME', defaultValue: 'todo-app', description: 'Docker image name')
        booleanParam(name: 'PUSH_IMAGE', defaultValue: true, description: 'Push to DockerHub?')
        booleanParam(name: 'PUSH_NEXUS', defaultValue: true, description: 'Push to Nexus?')
    }

    environment {
        // DockerHub
        DOCKERHUB_CREDS = credentials('mydoc')
        FULL_IMAGE      = "${DOCKERHUB_CREDS_USR}/${params.IMAGE_NAME}:${env.BUILD_NUMBER}"
        FULL_LATEST     = "${DOCKERHUB_CREDS_USR}/${params.IMAGE_NAME}:latest"

        // Nexus
        NEXUS_CREDS        = credentials('nexus-creds')
        NEXUS_URL          = 'local-nexus:8082'             // Docker registry port
        NEXUS_RAW_URL      = 'http://local-nexus:8081'      // Nexus UI/API base
        NEXUS_RAW_REPO     = 'todo-raw'                     // raw repo name you created
        NEXUS_DOCKER_IMAGE = "local-nexus:8082/${params.IMAGE_NAME}:${env.BUILD_NUMBER}"

        // Sonar
        SONAR_TOKEN = credentials('sonar-token')
    }

    stages {

        stage('Checkout') {
            steps {
                checkout scm
                echo "Branch: ${env.GIT_BRANCH} | Commit: ${env.GIT_COMMIT}"
            }
        }

        stage('Install Dependencies') {
            steps {
                sh 'pip install -r requirements.txt --break-system-packages -q'
            }
        }

        stage('Run Tests') {
            steps {
                sh '''
                    pytest -v \
                      --cov=app \
                      --cov-report=term-missing \
                      --cov-report=html:coverage-report \
                      --junitxml=test-results.xml
                '''
            }
            post {
                always {
                    junit 'test-results.xml'
                }
            }
        }

        stage('Publish Test Report to Nexus') {
            // Push the HTML coverage report as a zip to Nexus raw repo
            // So it's permanently stored and downloadable from Nexus UI
            when {
                expression { return params.PUSH_NEXUS }
            }
            steps {
                sh """
                    # Zip the HTML coverage report
                    zip -r coverage-report-${env.BUILD_NUMBER}.zip coverage-report/

                    # Upload to Nexus raw repo using curl
                    # Nexus raw upload URL format:
                    # POST /repository/<repo-name>/<path/to/file>
                    curl -u ${NEXUS_CREDS_USR}:${NEXUS_CREDS_PSW} \
                         --upload-file coverage-report-${env.BUILD_NUMBER}.zip \
                         ${NEXUS_RAW_URL}/repository/${NEXUS_RAW_REPO}/todo-app/build-${env.BUILD_NUMBER}/coverage-report.zip

                    echo "✅ Coverage report uploaded to Nexus"
                    echo "📦 View at: ${NEXUS_RAW_URL}/#browse/browse:${NEXUS_RAW_REPO}"
                """

                // Also archive in Jenkins UI as a quick download link
                archiveArtifacts artifacts: 'test-results.xml', fingerprint: true
            }
        }

        stage('SonarQube Analysis') {
            steps {
                sh """
                    pip install pysonar-scanner --break-system-packages -q
                    python -m pysonar_scanner \
                      -Dsonar.projectKey=todo-app \
                      -Dsonar.sources=. \
                      -Dsonar.host.url=http://local-sonar:9000 \
                      -Dsonar.token=${SONAR_TOKEN} \
                      -Dsonar.exclusions=tests/**
                """
            }
        }

        stage('Docker Build') {
            steps {
                sh """
                    # Build once, tag for both DockerHub and Nexus
                    docker build \
                      -t ${FULL_IMAGE} \
                      -t ${FULL_LATEST} \
                      -t ${NEXUS_DOCKER_IMAGE} \
                      .
                """
            }
        }

        stage('Push to DockerHub') {
            when {
                expression { return params.PUSH_IMAGE }
            }
            steps {
                sh """
                    echo ${DOCKERHUB_CREDS_PSW} | docker login -u ${DOCKERHUB_CREDS_USR} --password-stdin
                    docker push ${FULL_IMAGE}
                    docker push ${FULL_LATEST}
                    docker logout
                    echo "✅ Pushed to DockerHub: ${FULL_IMAGE}"
                """
            }
        }

        stage('Push to Nexus Docker Registry') {
            when {
                expression { return params.PUSH_NEXUS }
            }
            steps {
                sh """
                    # Login to Nexus Docker registry (port 8082)
                    echo ${NEXUS_CREDS_PSW} | docker login ${NEXUS_URL} \
                         -u ${NEXUS_CREDS_USR} --password-stdin

                    docker push ${NEXUS_DOCKER_IMAGE}

                    docker logout ${NEXUS_URL}
                    echo "✅ Pushed to Nexus: ${NEXUS_DOCKER_IMAGE}"
                    echo "📦 View at: ${NEXUS_RAW_URL}/#browse/browse:todo-docker"
                """
            }
        }

        stage('Smoke Test') {
            steps {
                sh """
                    docker rm -f todo-smoke || true
                    docker run -d --name todo-smoke -p 5001:5000 ${FULL_IMAGE}
                    sleep 3
                    curl -f http://localhost:5001/todos
                    docker rm -f todo-smoke
                    echo "✅ Smoke test passed"
                """
            }
        }
    }

    post {
        always {
            sh 'docker rm -f todo-smoke || true'
        }
        success {
            echo "✅ Done."
        }
        failure {
            echo "❌ Failed."
        }
    }
}