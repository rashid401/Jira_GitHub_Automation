pipeline {
    agent {
        docker {
            image 'blackdawn/python-ci:alpine'
            args '-v /var/run/docker.sock:/var/run/docker.sock'
        }
    }
    environment {
        IMAGE_NAME = "jira-github-automation"
        IMAGE_TAG = "V${BUILD_NUMBER}"
        SONAR_ENV = "sonarqube-server"
        DEPLOY_HOST = "ec2-user@xx.xx.xx.xx"
    }
    stages {
        stage ('Checkout') {
            steps {
                Checkout scm
            }
        }
        stage ('Lint & Unit Tests') {
            steps {
                dir(Jira_GitHub_Automation) {
                    sh '''
                        flake8 .
                        pytest tests --cov=. --cov-report=xml
                    '''
                }
            }
        }

        stage ('SonarQube Analysis') {
            steps {
                withSonarQubeEnv("${SONARQUBE_ENV}") {
                    sh '''
                        sonar-scanner \
                        -Dsonar.projectKey=jira-github-automation \
                        -Dsonar.projectName=Jira_github_automation \
                        -Dsonar.sources=Jira_GitHub_Automation \
                        -Dsonar.exclude=**/tests/** \
                        -Dsonar.python.coverage.reportPaths=coverage.xml
                    '''
                }
            }
        }
        stage('Quality Gate') {
            when {branch 'main'}
            steps {
                timeout(time: 5, unit: 'MINUTES') {
                    waitForSonarGate abortPipeline: true
                }
            }
        }
        stage('Docker Build') {
            steps {
                sh '''
                    docker build -t ${IMAGE_NAME}:${IMAGE_TAG} .
                    dockr tag ${IMAGE_NAME}:${IMAGE_TAG} blackdawn/${IMAGE_NAME}:${IMAGE_TAG}
                    docker push blackdawn/${IMAGE_NAME}:${IMAGE_TAG}
                '''
            }
        }
        stage('Deploy to EC2') {
            when {branch 'MAIN'}
            steps {
                sshagent(['ec2-ssh-key']){
                 sh '''
                    ssh ${DEPLOY_HOST} << EOF
                    set -e
                    mkdir -p /opt/jira-github-automation
                    cat > /opt/jira-github-automation/docker-compose.yml << 'COMPOSE_EOF'
                    $(cat docker-compose.yml)
                    COMPOSE_EOF
                    export IMAGE_TAG=${IMAGE_TAG}
                    cd /opt/jira-github-automation
                    docker-compose pull
                    docker-compose down || true
                    docker-compose up -d
                    EOF
                '''
                }
            }
        }
    }
    post {
        success {
            emailtext(
                subject: "SUCCESS: Jenkins Pipeline - ${JOB_NAME} #${BUILD_NUMBER}",
                body: "Pipeline succeeded. \n Build URL: ${BUILD_URL}",
                to: "rashidvn401@outlook.com"
            )
        }
        failure {
            emailtext(
                subject: "FAILED: Jenkins Pipeline - ${JOB_NAME} #${BUILD_NUMBER}",
                body: "Pipeline failed. \n Build URL: ${BUILD_URL}",
                to: "rashidvn401@outlook.com"
            )
        }
    }
}