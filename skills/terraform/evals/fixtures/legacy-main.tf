provider "aws" {
    region = "eu-west-1"
    access_key = "AKIAIOSFODNN7EXAMPLE"
    secret_key = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
}

variable "subnet_cidrs" {
  default = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
}

variable "db_password" {
  default = "SuperSecret123!"
}

resource "aws_vpc" "main_vpc" {
  cidr_block = "10.0.0.0/16"
}

resource "aws_subnet" "subnet" {
  count = length(var.subnet_cidrs)
  vpc_id     = aws_vpc.main_vpc.id
  cidr_block = element(var.subnet_cidrs, count.index)
}

resource "aws_instance" "web_instance" {
    ami           = "ami-0abcdef1234567890"
    instance_type = "t3.medium"
    subnet_id     = aws_subnet.subnet[0].id
    depends_on = [aws_vpc.main_vpc]
}

resource "aws_db_instance" "db" {
  identifier = "legacy-db"
  engine     = "postgres"
  instance_class = "db.t3.micro"
  allocated_storage = 20
  username = "admin"
  password = var.db_password
}
