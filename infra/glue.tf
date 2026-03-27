# --- Bronze Glue Catalog Tables ---
# External tables for Athena to query CDC JSON Lines data in S3.
# Partition projection auto-discovers year/month/day partitions.

locals {
  bronze_table_defaults = {
    input_format  = "org.apache.hadoop.mapred.TextInputFormat"
    output_format = "org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat"
    serde_library = "org.openx.data.jsonserde.JsonSerDe"
  }
}

# --- equipment ---

resource "aws_glue_catalog_table" "bronze_equipment" {
  database_name = aws_glue_catalog_database.ironlog.name
  name          = "bronze_equipment"
  table_type    = "EXTERNAL_TABLE"

  parameters = {
    "classification"            = "json"
    "compressionType"           = "gzip"
    "projection.enabled"        = "true"
    "projection.year.type"      = "integer"
    "projection.year.range"     = "2024,2030"
    "projection.month.type"     = "integer"
    "projection.month.range"    = "1,12"
    "projection.month.digits"   = "2"
    "projection.day.type"       = "integer"
    "projection.day.range"      = "1,31"
    "projection.day.digits"     = "2"
    "storage.location.template" = "s3://${aws_s3_bucket.data_lake.bucket}/bronze/equipment/year=$${year}/month=$${month}/day=$${day}/"
  }

  storage_descriptor {
    location      = "s3://${aws_s3_bucket.data_lake.bucket}/bronze/equipment/"
    input_format  = local.bronze_table_defaults.input_format
    output_format = local.bronze_table_defaults.output_format

    ser_de_info {
      serialization_library = local.bronze_table_defaults.serde_library
    }

    columns {
      name = "pk"
      type = "string"
    }
    columns {
      name = "sk"
      type = "string"
    }
    columns {
      name = "equipment_type"
      type = "string"
    }
    columns {
      name = "name"
      type = "string"
    }
    columns {
      name = "weight_kg"
      type = "double"
    }
    columns {
      name = "quantity"
      type = "int"
    }
    columns {
      name = "settings_schema"
      type = "string"
    }
    columns {
      name = "is_archived"
      type = "boolean"
    }
    columns {
      name = "created_at"
      type = "string"
    }
    columns {
      name = "updated_at"
      type = "string"
    }
    columns {
      name = "gsi1pk"
      type = "string"
    }
    columns {
      name = "gsi1sk"
      type = "string"
    }
    columns {
      name = "_cdc_event_name"
      type = "string"
    }
    columns {
      name = "_cdc_timestamp"
      type = "string"
    }
    columns {
      name = "_cdc_sequence_number"
      type = "string"
    }
  }

  partition_keys {
    name = "year"
    type = "string"
  }
  partition_keys {
    name = "month"
    type = "string"
  }
  partition_keys {
    name = "day"
    type = "string"
  }
}

# --- exercises ---

resource "aws_glue_catalog_table" "bronze_exercises" {
  database_name = aws_glue_catalog_database.ironlog.name
  name          = "bronze_exercises"
  table_type    = "EXTERNAL_TABLE"

  parameters = {
    "classification"            = "json"
    "compressionType"           = "gzip"
    "projection.enabled"        = "true"
    "projection.year.type"      = "integer"
    "projection.year.range"     = "2024,2030"
    "projection.month.type"     = "integer"
    "projection.month.range"    = "1,12"
    "projection.month.digits"   = "2"
    "projection.day.type"       = "integer"
    "projection.day.range"      = "1,31"
    "projection.day.digits"     = "2"
    "storage.location.template" = "s3://${aws_s3_bucket.data_lake.bucket}/bronze/exercises/year=$${year}/month=$${month}/day=$${day}/"
  }

  storage_descriptor {
    location      = "s3://${aws_s3_bucket.data_lake.bucket}/bronze/exercises/"
    input_format  = local.bronze_table_defaults.input_format
    output_format = local.bronze_table_defaults.output_format

    ser_de_info {
      serialization_library = local.bronze_table_defaults.serde_library
    }

    columns {
      name = "pk"
      type = "string"
    }
    columns {
      name = "sk"
      type = "string"
    }
    columns {
      name = "name"
      type = "string"
    }
    columns {
      name = "muscle_group"
      type = "string"
    }
    columns {
      name = "default_bar_id"
      type = "string"
    }
    columns {
      name = "has_plate_calculator"
      type = "boolean"
    }
    columns {
      name = "is_unilateral"
      type = "boolean"
    }
    columns {
      name = "weak_side"
      type = "string"
    }
    columns {
      name = "rest_timer_seconds"
      type = "int"
    }
    columns {
      name = "machine_settings"
      type = "string"
    }
    columns {
      name = "replacement_exercise_ids"
      type = "array<string>"
    }
    columns {
      name = "notes"
      type = "string"
    }
    columns {
      name = "is_archived"
      type = "boolean"
    }
    columns {
      name = "created_at"
      type = "string"
    }
    columns {
      name = "updated_at"
      type = "string"
    }
    columns {
      name = "gsi1pk"
      type = "string"
    }
    columns {
      name = "gsi1sk"
      type = "string"
    }
    columns {
      name = "_cdc_event_name"
      type = "string"
    }
    columns {
      name = "_cdc_timestamp"
      type = "string"
    }
    columns {
      name = "_cdc_sequence_number"
      type = "string"
    }
  }

  partition_keys {
    name = "year"
    type = "string"
  }
  partition_keys {
    name = "month"
    type = "string"
  }
  partition_keys {
    name = "day"
    type = "string"
  }
}

# --- sessions ---

resource "aws_glue_catalog_table" "bronze_sessions" {
  database_name = aws_glue_catalog_database.ironlog.name
  name          = "bronze_sessions"
  table_type    = "EXTERNAL_TABLE"

  parameters = {
    "classification"            = "json"
    "compressionType"           = "gzip"
    "projection.enabled"        = "true"
    "projection.year.type"      = "integer"
    "projection.year.range"     = "2024,2030"
    "projection.month.type"     = "integer"
    "projection.month.range"    = "1,12"
    "projection.month.digits"   = "2"
    "projection.day.type"       = "integer"
    "projection.day.range"      = "1,31"
    "projection.day.digits"     = "2"
    "storage.location.template" = "s3://${aws_s3_bucket.data_lake.bucket}/bronze/sessions/year=$${year}/month=$${month}/day=$${day}/"
  }

  storage_descriptor {
    location      = "s3://${aws_s3_bucket.data_lake.bucket}/bronze/sessions/"
    input_format  = local.bronze_table_defaults.input_format
    output_format = local.bronze_table_defaults.output_format

    ser_de_info {
      serialization_library = local.bronze_table_defaults.serde_library
    }

    columns {
      name = "pk"
      type = "string"
    }
    columns {
      name = "sk"
      type = "string"
    }
    columns {
      name = "plan_id"
      type = "string"
    }
    columns {
      name = "plan_day_number"
      type = "int"
    }
    columns {
      name = "date"
      type = "string"
    }
    columns {
      name = "status"
      type = "string"
    }
    columns {
      name = "started_at"
      type = "string"
    }
    columns {
      name = "completed_at"
      type = "string"
    }
    columns {
      name = "notes"
      type = "string"
    }
    columns {
      name = "created_at"
      type = "string"
    }
    columns {
      name = "gsi1pk"
      type = "string"
    }
    columns {
      name = "gsi1sk"
      type = "string"
    }
    columns {
      name = "_cdc_event_name"
      type = "string"
    }
    columns {
      name = "_cdc_timestamp"
      type = "string"
    }
    columns {
      name = "_cdc_sequence_number"
      type = "string"
    }
  }

  partition_keys {
    name = "year"
    type = "string"
  }
  partition_keys {
    name = "month"
    type = "string"
  }
  partition_keys {
    name = "day"
    type = "string"
  }
}

# --- sets ---

resource "aws_glue_catalog_table" "bronze_sets" {
  database_name = aws_glue_catalog_database.ironlog.name
  name          = "bronze_sets"
  table_type    = "EXTERNAL_TABLE"

  parameters = {
    "classification"            = "json"
    "compressionType"           = "gzip"
    "projection.enabled"        = "true"
    "projection.year.type"      = "integer"
    "projection.year.range"     = "2024,2030"
    "projection.month.type"     = "integer"
    "projection.month.range"    = "1,12"
    "projection.month.digits"   = "2"
    "projection.day.type"       = "integer"
    "projection.day.range"      = "1,31"
    "projection.day.digits"     = "2"
    "storage.location.template" = "s3://${aws_s3_bucket.data_lake.bucket}/bronze/sets/year=$${year}/month=$${month}/day=$${day}/"
  }

  storage_descriptor {
    location      = "s3://${aws_s3_bucket.data_lake.bucket}/bronze/sets/"
    input_format  = local.bronze_table_defaults.input_format
    output_format = local.bronze_table_defaults.output_format

    ser_de_info {
      serialization_library = local.bronze_table_defaults.serde_library
    }

    columns {
      name = "pk"
      type = "string"
    }
    columns {
      name = "sk"
      type = "string"
    }
    columns {
      name = "exercise_id"
      type = "string"
    }
    columns {
      name = "original_exercise_id"
      type = "string"
    }
    columns {
      name = "set_type"
      type = "string"
    }
    columns {
      name = "set_order"
      type = "int"
    }
    columns {
      name = "weight_kg"
      type = "double"
    }
    columns {
      name = "reps"
      type = "int"
    }
    columns {
      name = "rir"
      type = "int"
    }
    columns {
      name = "is_weight_pr"
      type = "boolean"
    }
    columns {
      name = "is_e1rm_pr"
      type = "boolean"
    }
    columns {
      name = "estimated_1rm"
      type = "double"
    }
    columns {
      name = "timestamp"
      type = "string"
    }
    columns {
      name = "gsi1pk"
      type = "string"
    }
    columns {
      name = "gsi1sk"
      type = "string"
    }
    columns {
      name = "_cdc_event_name"
      type = "string"
    }
    columns {
      name = "_cdc_timestamp"
      type = "string"
    }
    columns {
      name = "_cdc_sequence_number"
      type = "string"
    }
  }

  partition_keys {
    name = "year"
    type = "string"
  }
  partition_keys {
    name = "month"
    type = "string"
  }
  partition_keys {
    name = "day"
    type = "string"
  }
}

# --- plans ---

resource "aws_glue_catalog_table" "bronze_plans" {
  database_name = aws_glue_catalog_database.ironlog.name
  name          = "bronze_plans"
  table_type    = "EXTERNAL_TABLE"

  parameters = {
    "classification"            = "json"
    "compressionType"           = "gzip"
    "projection.enabled"        = "true"
    "projection.year.type"      = "integer"
    "projection.year.range"     = "2024,2030"
    "projection.month.type"     = "integer"
    "projection.month.range"    = "1,12"
    "projection.month.digits"   = "2"
    "projection.day.type"       = "integer"
    "projection.day.range"      = "1,31"
    "projection.day.digits"     = "2"
    "storage.location.template" = "s3://${aws_s3_bucket.data_lake.bucket}/bronze/plans/year=$${year}/month=$${month}/day=$${day}/"
  }

  storage_descriptor {
    location      = "s3://${aws_s3_bucket.data_lake.bucket}/bronze/plans/"
    input_format  = local.bronze_table_defaults.input_format
    output_format = local.bronze_table_defaults.output_format

    ser_de_info {
      serialization_library = local.bronze_table_defaults.serde_library
    }

    columns {
      name = "pk"
      type = "string"
    }
    columns {
      name = "sk"
      type = "string"
    }
    columns {
      name = "name"
      type = "string"
    }
    columns {
      name = "split_type"
      type = "string"
    }
    columns {
      name = "is_active"
      type = "boolean"
    }
    columns {
      name = "created_at"
      type = "string"
    }
    columns {
      name = "updated_at"
      type = "string"
    }
    columns {
      name = "gsi1pk"
      type = "string"
    }
    columns {
      name = "gsi1sk"
      type = "string"
    }
    columns {
      name = "_cdc_event_name"
      type = "string"
    }
    columns {
      name = "_cdc_timestamp"
      type = "string"
    }
    columns {
      name = "_cdc_sequence_number"
      type = "string"
    }
  }

  partition_keys {
    name = "year"
    type = "string"
  }
  partition_keys {
    name = "month"
    type = "string"
  }
  partition_keys {
    name = "day"
    type = "string"
  }
}

# --- plan_days ---

resource "aws_glue_catalog_table" "bronze_plan_days" {
  database_name = aws_glue_catalog_database.ironlog.name
  name          = "bronze_plan_days"
  table_type    = "EXTERNAL_TABLE"

  parameters = {
    "classification"            = "json"
    "compressionType"           = "gzip"
    "projection.enabled"        = "true"
    "projection.year.type"      = "integer"
    "projection.year.range"     = "2024,2030"
    "projection.month.type"     = "integer"
    "projection.month.range"    = "1,12"
    "projection.month.digits"   = "2"
    "projection.day.type"       = "integer"
    "projection.day.range"      = "1,31"
    "projection.day.digits"     = "2"
    "storage.location.template" = "s3://${aws_s3_bucket.data_lake.bucket}/bronze/plan_days/year=$${year}/month=$${month}/day=$${day}/"
  }

  storage_descriptor {
    location      = "s3://${aws_s3_bucket.data_lake.bucket}/bronze/plan_days/"
    input_format  = local.bronze_table_defaults.input_format
    output_format = local.bronze_table_defaults.output_format

    ser_de_info {
      serialization_library = local.bronze_table_defaults.serde_library
    }

    columns {
      name = "pk"
      type = "string"
    }
    columns {
      name = "sk"
      type = "string"
    }
    columns {
      name = "day_name"
      type = "string"
    }
    columns {
      name = "exercises"
      type = "array<struct<exercise_id:string,order:int,target_sets:int,target_reps:string,set_type:string>>"
    }
    columns {
      name = "gsi1pk"
      type = "string"
    }
    columns {
      name = "gsi1sk"
      type = "string"
    }
    columns {
      name = "_cdc_event_name"
      type = "string"
    }
    columns {
      name = "_cdc_timestamp"
      type = "string"
    }
    columns {
      name = "_cdc_sequence_number"
      type = "string"
    }
  }

  partition_keys {
    name = "year"
    type = "string"
  }
  partition_keys {
    name = "month"
    type = "string"
  }
  partition_keys {
    name = "day"
    type = "string"
  }
}

# --- corrections ---

resource "aws_glue_catalog_table" "bronze_corrections" {
  database_name = aws_glue_catalog_database.ironlog.name
  name          = "bronze_corrections"
  table_type    = "EXTERNAL_TABLE"

  parameters = {
    "classification"            = "json"
    "compressionType"           = "gzip"
    "projection.enabled"        = "true"
    "projection.year.type"      = "integer"
    "projection.year.range"     = "2024,2030"
    "projection.month.type"     = "integer"
    "projection.month.range"    = "1,12"
    "projection.month.digits"   = "2"
    "projection.day.type"       = "integer"
    "projection.day.range"      = "1,31"
    "projection.day.digits"     = "2"
    "storage.location.template" = "s3://${aws_s3_bucket.data_lake.bucket}/bronze/corrections/year=$${year}/month=$${month}/day=$${day}/"
  }

  storage_descriptor {
    location      = "s3://${aws_s3_bucket.data_lake.bucket}/bronze/corrections/"
    input_format  = local.bronze_table_defaults.input_format
    output_format = local.bronze_table_defaults.output_format

    ser_de_info {
      serialization_library = local.bronze_table_defaults.serde_library
    }

    columns {
      name = "pk"
      type = "string"
    }
    columns {
      name = "sk"
      type = "string"
    }
    columns {
      name = "session_id"
      type = "string"
    }
    columns {
      name = "field"
      type = "string"
    }
    columns {
      name = "old_value"
      type = "string"
    }
    columns {
      name = "new_value"
      type = "string"
    }
    columns {
      name = "reason"
      type = "string"
    }
    columns {
      name = "created_at"
      type = "string"
    }
    columns {
      name = "gsi1pk"
      type = "string"
    }
    columns {
      name = "gsi1sk"
      type = "string"
    }
    columns {
      name = "_cdc_event_name"
      type = "string"
    }
    columns {
      name = "_cdc_timestamp"
      type = "string"
    }
    columns {
      name = "_cdc_sequence_number"
      type = "string"
    }
  }

  partition_keys {
    name = "year"
    type = "string"
  }
  partition_keys {
    name = "month"
    type = "string"
  }
  partition_keys {
    name = "day"
    type = "string"
  }
}

# --- session_exercise_notes ---

resource "aws_glue_catalog_table" "bronze_session_exercise_notes" {
  database_name = aws_glue_catalog_database.ironlog.name
  name          = "bronze_session_exercise_notes"
  table_type    = "EXTERNAL_TABLE"

  parameters = {
    "classification"            = "json"
    "compressionType"           = "gzip"
    "projection.enabled"        = "true"
    "projection.year.type"      = "integer"
    "projection.year.range"     = "2024,2030"
    "projection.month.type"     = "integer"
    "projection.month.range"    = "1,12"
    "projection.month.digits"   = "2"
    "projection.day.type"       = "integer"
    "projection.day.range"      = "1,31"
    "projection.day.digits"     = "2"
    "storage.location.template" = "s3://${aws_s3_bucket.data_lake.bucket}/bronze/session_exercise_notes/year=$${year}/month=$${month}/day=$${day}/"
  }

  storage_descriptor {
    location      = "s3://${aws_s3_bucket.data_lake.bucket}/bronze/session_exercise_notes/"
    input_format  = local.bronze_table_defaults.input_format
    output_format = local.bronze_table_defaults.output_format

    ser_de_info {
      serialization_library = local.bronze_table_defaults.serde_library
    }

    columns {
      name = "pk"
      type = "string"
    }
    columns {
      name = "sk"
      type = "string"
    }
    columns {
      name = "note_text"
      type = "string"
    }
    columns {
      name = "created_at"
      type = "string"
    }
    columns {
      name = "_cdc_event_name"
      type = "string"
    }
    columns {
      name = "_cdc_timestamp"
      type = "string"
    }
    columns {
      name = "_cdc_sequence_number"
      type = "string"
    }
  }

  partition_keys {
    name = "year"
    type = "string"
  }
  partition_keys {
    name = "month"
    type = "string"
  }
  partition_keys {
    name = "day"
    type = "string"
  }
}

# --- WHOOP recovery ---

resource "aws_glue_catalog_table" "bronze_recovery" {
  database_name = aws_glue_catalog_database.ironlog.name
  name          = "bronze_recovery"
  table_type    = "EXTERNAL_TABLE"

  parameters = {
    "classification"            = "json"
    "compressionType"           = "gzip"
    "projection.enabled"        = "true"
    "projection.year.type"      = "integer"
    "projection.year.range"     = "2024,2030"
    "projection.month.type"     = "integer"
    "projection.month.range"    = "1,12"
    "projection.month.digits"   = "2"
    "projection.day.type"       = "integer"
    "projection.day.range"      = "1,31"
    "projection.day.digits"     = "2"
    "storage.location.template" = "s3://${aws_s3_bucket.data_lake.bucket}/bronze/recovery/year=$${year}/month=$${month}/day=$${day}/"
  }

  storage_descriptor {
    location      = "s3://${aws_s3_bucket.data_lake.bucket}/bronze/recovery/"
    input_format  = local.bronze_table_defaults.input_format
    output_format = local.bronze_table_defaults.output_format

    ser_de_info {
      serialization_library = local.bronze_table_defaults.serde_library
    }

    columns {
      name = "cycle_id"
      type = "bigint"
    }
    columns {
      name = "sleep_id"
      type = "string"
    }
    columns {
      name = "user_id"
      type = "bigint"
    }
    columns {
      name = "score_state"
      type = "string"
    }
    columns {
      name = "score"
      type = "struct<user_calibrating:boolean,recovery_score:double,resting_heart_rate:double,hrv_rmssd_milli:double,spo2_percentage:double,skin_temp_celsius:double>"
    }
    columns {
      name = "created_at"
      type = "string"
    }
    columns {
      name = "updated_at"
      type = "string"
    }
    columns {
      name = "_sync_timestamp"
      type = "string"
    }
  }

  partition_keys {
    name = "year"
    type = "string"
  }
  partition_keys {
    name = "month"
    type = "string"
  }
  partition_keys {
    name = "day"
    type = "string"
  }
}

# --- WHOOP sleep ---

resource "aws_glue_catalog_table" "bronze_sleep" {
  database_name = aws_glue_catalog_database.ironlog.name
  name          = "bronze_sleep"
  table_type    = "EXTERNAL_TABLE"

  parameters = {
    "classification"            = "json"
    "compressionType"           = "gzip"
    "projection.enabled"        = "true"
    "projection.year.type"      = "integer"
    "projection.year.range"     = "2024,2030"
    "projection.month.type"     = "integer"
    "projection.month.range"    = "1,12"
    "projection.month.digits"   = "2"
    "projection.day.type"       = "integer"
    "projection.day.range"      = "1,31"
    "projection.day.digits"     = "2"
    "storage.location.template" = "s3://${aws_s3_bucket.data_lake.bucket}/bronze/sleep/year=$${year}/month=$${month}/day=$${day}/"
  }

  storage_descriptor {
    location      = "s3://${aws_s3_bucket.data_lake.bucket}/bronze/sleep/"
    input_format  = local.bronze_table_defaults.input_format
    output_format = local.bronze_table_defaults.output_format

    ser_de_info {
      serialization_library = local.bronze_table_defaults.serde_library
    }

    columns {
      name = "id"
      type = "string"
    }
    columns {
      name = "cycle_id"
      type = "bigint"
    }
    columns {
      name = "user_id"
      type = "bigint"
    }
    columns {
      name = "start"
      type = "string"
    }
    columns {
      name = "end"
      type = "string"
    }
    columns {
      name = "nap"
      type = "boolean"
    }
    columns {
      name = "score_state"
      type = "string"
    }
    columns {
      name = "score"
      type = "struct<stage_summary:struct<total_in_bed_time_milli:bigint,total_awake_time_milli:bigint,total_no_data_time_milli:bigint,total_light_sleep_time_milli:bigint,total_slow_wave_sleep_time_milli:bigint,total_rem_sleep_time_milli:bigint,sleep_cycle_count:int,disturbance_count:int>,respiratory_rate:double,sleep_performance_percentage:double,sleep_consistency_percentage:double,sleep_efficiency_percentage:double>"
    }
    columns {
      name = "created_at"
      type = "string"
    }
    columns {
      name = "updated_at"
      type = "string"
    }
    columns {
      name = "_sync_timestamp"
      type = "string"
    }
  }

  partition_keys {
    name = "year"
    type = "string"
  }
  partition_keys {
    name = "month"
    type = "string"
  }
  partition_keys {
    name = "day"
    type = "string"
  }
}
