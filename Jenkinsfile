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
        stage('Docker Build & Push') {
            steps {
                sh '''
                    docker build -t ${IMAGE_NAME}:${IMAGE_TAG} .
                    dockr tag ${IMAGE_NAME}:${IMAGE_TAG} blackdawn/${IMAGE_NAME}:${IMAGE_TAG}
                    docker push blackdawn/${IMAGE_NAME}:${IMAGE_TAG}
                '''
            }
        }
        stage('Terraform Apply & Get Host') {
            steps {
                dir('terraform') {
                    script {
                        sh '''
                        terraform init
                        terraform apply -auto-approve
                        '''

                        def ip = sh(
                            script: "terraform outout -raw ec2_public_ip",
                            returnStdout: true
                        ).trim()

                        env.DEPLOY_HOST = "ec2-user@{ip}"
                    }
                }
            }
        }
        stage('Deploy to EC2') {
            when {branch 'main'}
            steps {
                sshagent(['ec2-ssh-key']){
                 sh '''
                    ssh -o StrictHostKeyChecking=no ${DEPLOY_HOST} '
                      set -e
                      mkdir -p /opt/jira-github-automation
                    '
                    scp docker-compose.yml ${DEPLOY_HOST}:/opt/jira-github-automation/docker-compose.yml
                    scp docker-compose.yml ${DEPLOY_HOST}:/opt/jira-github-automation/deploy.sh

                    ssh -o StrictHostKeyChecking=no ${DEPLOY_HOST} '
                      chmod +x /opt/jira-github-automation/deploy.sh
                      export IMAGE_TAG=${IMAGE_TAG}
                      /opt/jira-github-automation/deploy.sh
                    '
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