---
title: "AWS를 활용해 웹 서비스 개발하기(1)"
excerpt: "AWS를 활용해 웹 서비스 개발하기"

categories:
    - study
header:
  teaser: "/assets/images/aws.jpg"
last_modified_at: 2025-09-21
---

AWS가 제공하는 PaaS들을 사용하여 웹 서비스를 만들어 보려고 한다.<br/>
이번 포스팅에서 다룬 내용은 Cognito를 연동한 간단한 API 서버를 ECS를 통해
배포하는 것을 목표로 했다.

<hr>

### [user_service.go]

```go
package main

import (
	"context"
	"crypto/hmac"
	"crypto/sha256"
	"encoding/base64"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"time"

	"github.com/aws/aws-sdk-go-v2/aws"
	"github.com/aws/aws-sdk-go-v2/config"
	"github.com/aws/aws-sdk-go-v2/service/cognitoidentityprovider"
	"github.com/aws/aws-sdk-go-v2/service/cognitoidentityprovider/types"
)

// HMAC-SHA256을 사용하여 SECRET_HASH 계산
func calculateSecretHash(clientID, clientSecret, username string) string {
	message := username + clientID
	hash := hmac.New(sha256.New, []byte(clientSecret))
	hash.Write([]byte(message))
	return base64.StdEncoding.EncodeToString(hash.Sum(nil))
}

type UserService struct {
	cognitoClient *cognitoidentityprovider.Client
	userPoolID    string
	clientID      string
	clientSecret  string
}

type SignUpRequest struct {
	Email    string `json:"email"`
	Password string `json:"password"`
	NickName string `json:"nickname"`
}

type SignInRequest struct {
	Email    string `json:"email"`
	Password string `json:"password"`
}

// HealthCheck 핸들러
func (s *UserService) HealthHandler(w http.ResponseWriter, r *http.Request) {
	w.WriteHeader(http.StatusOK)
	w.Write([]byte("OK"))
}

// SignUp 핸들러
func (s *UserService) SignUpHandler(w http.ResponseWriter, r *http.Request) {
	var req SignUpRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid request payload", http.StatusBadRequest)
		return
	}

	secretHash := calculateSecretHash(s.clientID, s.clientSecret, req.Email)
	input := &cognitoidentityprovider.SignUpInput{
		ClientId:   &s.clientID,
		Username:   &req.Email,
		Password:   &req.Password,
		SecretHash: &secretHash,
		UserAttributes: []types.AttributeType{
			{
				Name:  aws.String("nickname"),
				Value: aws.String(req.NickName),
			},
		},
	}

	_, err := s.cognitoClient.SignUp(r.Context(), input)
	if err != nil {
		http.Error(w, fmt.Sprintf("Failed to sign up: %v", err), http.StatusInternalServerError)
		return
	}

	w.WriteHeader(http.StatusCreated)
	json.NewEncoder(w).Encode(map[string]string{"message": "User signed up successfully!"})
}

// SignIn 핸들러
func (s *UserService) SignInHandler(w http.ResponseWriter, r *http.Request) {
	var req SignInRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid request payload", http.StatusBadRequest)
		return
	}

	secretHash := calculateSecretHash(s.clientID, s.clientSecret, req.Email)
	input := &cognitoidentityprovider.InitiateAuthInput{
		AuthFlow: "USER_PASSWORD_AUTH",
		AuthParameters: map[string]string{
			"USERNAME":    req.Email,
			"PASSWORD":    req.Password,
			"SECRET_HASH": secretHash,
		},
		ClientId: &s.clientID,
	}

	output, err := s.cognitoClient.InitiateAuth(r.Context(), input)
	if err != nil {
		http.Error(w, fmt.Sprintf("Failed to sign in: %v", err), http.StatusUnauthorized)
		return
	}

	json.NewEncoder(w).Encode(map[string]string{"token": *output.AuthenticationResult.IdToken})
}

func loggingMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		start := time.Now()
		log.Printf("Started %s %s from %s", r.Method, r.URL.String(), r.RemoteAddr)
		next.ServeHTTP(w, r)
		duration := time.Since(start)
		log.Printf("Completed %s %s in %v", r.Method, r.URL.String(), duration)
	})
}

func main() {
	cfg, err := config.LoadDefaultConfig(context.TODO(), config.WithRegion("<Region>"))
	if err != nil {
		panic("unable to load AWS SDK config")
	}

	cognitoClient := cognitoidentityprovider.NewFromConfig(cfg)

	userService := &UserService{
		cognitoClient: cognitoClient,
		userPoolID:    "<userPoolID>", // AWS Cognito User Pool 클라이언트 ID
		clientID:      "<clientID>",   // AWS clientID
		clientSecret:  "<clientSecret>", // AWS Client Secret
	}

	mux := http.NewServeMux()
	mux.HandleFunc("/signup", userService.SignUpHandler)
	mux.HandleFunc("/signin", userService.SignInHandler)

    // For ALB(Application Load Balancer) Health Check
	mux.HandleFunc("/health", userService.HealthHandler)

	port := "8080"

	log.Printf("Server is running on port :%s\n", port)
	log.Fatal(http.ListenAndServe(":"+port, loggingMiddleware(mux)))
}

```

나는 congito에 email, password, nickname을 필수로 설정했기 때문에
Request로 해당 값을 받도록 하였다.

### [Dockerfile]

```Dockerfile
# Stage 1: Build the application
FROM golang:1.22-alpine AS builder

WORKDIR /app

# Install necessary build tools
RUN apk add --no-cache gcc musl-dev

# Copy go.mod and go.sum
COPY go.mod go.sum ./

# Download dependencies
RUN go mod download

# Copy the application source code
COPY . .

# Build the binary statically linked
RUN go build -o user_service .

# Stage 2: Create a minimal runtime image
FROM alpine:latest

WORKDIR /app

# Copy the built binary from the builder stage
COPY --from=builder /app/user_service .

# Expose the port
EXPOSE 8080

# Run the application
CMD ["./user_service"]
```

도커 이미지를 빌드하고 로컬에서 테스트 해보자 <br/>
```
docker build -t user_service .
docker run -p 8080:8080 user_service
```

요청
```
curl -X POST http://localhost:8080/signup -H "Content-Type: application/json" -d "{\"email\":\"20250201test@example.com\", \"password\":\"ThisisLocalTest1234@\", \"nickname\":\"KIMMUSIC\"}"
```

응답
```
{"message":"User signed up successfully!"}
```

정상적으로 응답되고 Cognito에 사용자 등록이 정상적으로 응록된 모습을 볼 수 있다.
![image](https://github.com/KIMMUSIC/kimmusic.github.io/blob/master/_posts/Images/localtest_cognito.PNG?raw=true)

이제 ECR(Elastic Container Registry)에 해당 이미지를 push 해보자

```
docker tag user_service:latest <AWS_ACCOUNT_ID>.dkr.ecr.ap-northeast-2.amazonaws.com/user_service:latest

docker push <AWS_ACCOUNT_ID>.dkr.ecr.ap-northeast-2.amazonaws.com/user_service:latest
```

ECR에 정상적으로 이미지가 올라간 모습을 볼 수 있다.
![image](https://github.com/KIMMUSIC/kimmusic.github.io/blob/master/_posts/Images/ECR.PNG?raw=true)

이제 ECS에서 클러스터, 태스크, 서비스를 생성해보자

#### [ECS]
나는 EC2 인스턴스를 사용하여 구성하였다.

![image](https://github.com/KIMMUSIC/kimmusic.github.io/blob/master/_posts/Images/cluster.PNG?raw=true)

인스턴스 생성 후 태스크 정의를 생성하자<br/>
태스크 정의 역시 EC2 인스턴스를 사용했으며 awsvpc 모드를 사용했다.

ECR에 올려둔 이미지 URI를 입력하고 8080 포트와 매핑한다.

![image](https://github.com/KIMMUSIC/kimmusic.github.io/blob/master/_posts/Images/task_def.PNG?raw=true)

태스크 정의를 생성 했다면 서비스를 생성하여 해당 태스크 정의를 실행하자.






