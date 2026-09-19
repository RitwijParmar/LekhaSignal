terraform { required_providers { snowflake = { source = "Snowflake-Labs/snowflake", version = "~> 1.0" } } }
variable "snowflake_account" { type = string }
variable "snowflake_user" { type = string }
provider "snowflake" { account = var.snowflake_account user = var.snowflake_user authenticator = "SNOWFLAKE_JWT" }
resource "snowflake_warehouse" "transform" { name = "LEKHASIGNAL_TRANSFORM_WH" warehouse_size = "SMALL" auto_suspend = 60 auto_resume = true }
resource "snowflake_database" "platform" { name = "LEKHASIGNAL" }
