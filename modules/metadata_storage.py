"""
Metadata Storage Module
Stores build metadata in DynamoDB or S3
"""

import json
import logging
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime


class MetadataStorage:
    """Store build metadata in DynamoDB or S3"""
    
    def __init__(self, config: Dict):
        """Initialize the metadata storage"""
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.storage_type = config.get('metadata_storage', {}).get('type', 'local')
        self.s3_config = config.get('s3', {})
        self.dynamodb_config = config.get('dynamodb', {})
        self.local_storage_dir = Path(__file__).parent.parent / 'metadata'
        self.local_storage_dir.mkdir(exist_ok=True)
    
    def store(self, build_metadata: Dict) -> bool:
        """
        Store build metadata
        
        Args:
            build_metadata: Build metadata to store
        
        Returns:
            bool: True if storage successful, False otherwise
        """
        if self.storage_type == 's3':
            return self._store_to_s3(build_metadata)
        elif self.storage_type == 'dynamodb':
            return self._store_to_dynamodb(build_metadata)
        else:
            return self._store_to_local(build_metadata)
    
    def _store_to_local(self, build_metadata: Dict) -> bool:
        """Store metadata to local file system"""
        try:
            self.logger.info("Storing metadata to local file system...")
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            image_name = build_metadata.get('image_name', 'unknown').replace('/', '_')
            filename = f"metadata_{image_name}_{timestamp}.json"
            
            metadata_path = self.local_storage_dir / filename
            
            with open(metadata_path, 'w') as f:
                json.dump(build_metadata, f, indent=2, default=str)
            
            self.logger.info(f"Metadata stored at {metadata_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error storing metadata locally: {str(e)}")
            return False
    
    def _store_to_s3(self, build_metadata: Dict) -> bool:
        """Store metadata to S3"""
        try:
            import boto3
            self.logger.info("Storing metadata to S3...")
            
            bucket_name = self.s3_config.get('bucket_name')
            if not bucket_name:
                self.logger.error("S3 bucket name not configured")
                return False
            
            # Initialize S3 client
            s3_client = boto3.client(
                's3',
                region_name=self.s3_config.get('region', 'us-east-1')
            )
            
            # Generate S3 key
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            image_name = build_metadata.get('image_name', 'unknown').replace('/', '_')
            key = f"docker-image-factory/metadata/{image_name}_{timestamp}.json"
            
            # Upload to S3
            s3_client.put_object(
                Bucket=bucket_name,
                Key=key,
                Body=json.dumps(build_metadata, indent=2, default=str),
                ContentType='application/json'
            )
            
            self.logger.info(f"Metadata stored to S3: s3://{bucket_name}/{key}")
            return True
            
        except ImportError:
            self.logger.error("boto3 not installed. Install with: pip install boto3")
            return False
        except Exception as e:
            self.logger.error(f"Error storing metadata to S3: {str(e)}")
            return False
    
    def _store_to_dynamodb(self, build_metadata: Dict) -> bool:
        """Store metadata to DynamoDB"""
        try:
            import boto3
            self.logger.info("Storing metadata to DynamoDB...")
            
            table_name = self.dynamodb_config.get('table_name')
            if not table_name:
                self.logger.error("DynamoDB table name not configured")
                return False
            
            # Initialize DynamoDB client
            dynamodb = boto3.resource(
                'dynamodb',
                region_name=self.dynamodb_config.get('region', 'us-east-1')
            )
            
            table = dynamodb.Table(table_name)
            
            # Generate item key
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            image_name = build_metadata.get('image_name', 'unknown')
            
            # Prepare item for DynamoDB
            item = {
                'image_name': image_name,
                'timestamp': timestamp,
                'build_metadata': json.dumps(build_metadata, default=str)
            }
            
            # Add all other metadata fields
            for key, value in build_metadata.items():
                if key not in ['image_name', 'timestamp']:
                    item[key] = value
            
            # Put item to DynamoDB
            table.put_item(Item=item)
            
            self.logger.info(f"Metadata stored to DynamoDB table: {table_name}")
            return True
            
        except ImportError:
            self.logger.error("boto3 not installed. Install with: pip install boto3")
            return False
        except Exception as e:
            self.logger.error(f"Error storing metadata to DynamoDB: {str(e)}")
            return False
