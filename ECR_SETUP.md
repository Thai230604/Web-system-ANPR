# AWS ECR Setup Guide

## 1. Tạo ECR Repository trên AWS Console

1. Đăng nhập AWS Console
2. Tìm service **ECR (Elastic Container Registry)**
3. Click **Create repository**
   - Repository name: `anpr-backend`
   - Visibility: Private
   - Tag immutability: Disabled (hoặc Enabled nếu muốn)
   - Scan on push: Enabled (optional)
   - Click **Create repository**

## 2. Tạo IAM User cho GitHub Actions

1. Vào **IAM** → **Users** → **Create user**
   - User name: `github-actions-ecr`
   - Không cần console access

2. Attach policies cho user:
   - `AmazonEC2ContainerRegistryPowerUser`
   - Hoặc tạo custom policy:
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Effect": "Allow",
         "Action": [
           "ecr:GetAuthorizationToken",
           "ecr:BatchCheckLayerAvailability",
           "ecr:GetDownloadUrlForLayer",
           "ecr:BatchGetImage",
           "ecr:PutImage",
           "ecr:InitiateLayerUpload",
           "ecr:UploadLayerPart",
           "ecr:CompleteLayerUpload",
           "ecr:DescribeRepositories"
         ],
         "Resource": "*"
       }
     ]
   }
   ```

3. Tạo **Access Key**:
   - Vào user vừa tạo → **Security credentials** → **Create access key**
   - Use case: Application running outside AWS
   - Lưu lại:
     - Access Key ID
     - Secret Access Key

## 3. Cập nhật GitHub Secrets

Vào repository GitHub → **Settings** → **Secrets and variables** → **Actions**

Thêm/Cập nhật các secrets:

### Secrets mới (AWS ECR):
- `AWS_ACCESS_KEY_ID`: Access Key ID vừa tạo
- `AWS_SECRET_ACCESS_KEY`: Secret Access Key vừa tạo

### Secrets giữ nguyên:
- `DB_HOST`
- `DB_PORT`
- `DB_USER`
- `DB_PASSWORD`
- `DB_NAME`
- `SECRET_KEY`
- `EC2_HOST`
- `EC2_USER`
- `EC2_KEY`

### Secrets có thể XÓA (không dùng Docker Hub nữa):
- ~~`DOCKER_USERNAME`~~
- ~~`DOCKER_PASSWORD`~~

## 4. Cấu hình AWS Region (optional)

Nếu ECR không ở `ap-southeast-1` (Singapore), sửa trong `.github/workflows/deploy.yml`:
```yaml
env:
  AWS_REGION: us-east-1  # Hoặc region của bạn
```

## 5. EC2 cần có IAM Role (Optional nhưng recommended)

Thay vì dùng access key trên EC2, nên:
1. Tạo **IAM Role** cho EC2:
   - Trust relationship: EC2
   - Policy: `AmazonEC2ContainerRegistryReadOnly`

2. Attach role vào EC2 instance:
   - EC2 Console → Select instance → Actions → Security → Modify IAM role

Nếu dùng IAM role, không cần cấu hình AWS CLI credentials trên EC2.

## 6. Kiểm tra

Push code lên GitHub và xem workflow chạy. Nếu thành công:
- Build image và push lên ECR
- Deploy lên EC2 và pull từ ECR

## Lợi ích của ECR:
✅ Không giới hạn bandwidth như Docker Hub
✅ Tốc độ pull/push nhanh hơn (cùng region)
✅ Tích hợp tốt với AWS services
✅ Image scanning tự động
✅ Không bị rate limit

## Chi phí:
- **Storage**: $0.10/GB/tháng
- **Data Transfer**: 
  - Pull trong cùng region: FREE
  - Pull ra internet: $0.09/GB (sau 1GB đầu free)
- Ước tính: ~$1-2/tháng cho project nhỏ
