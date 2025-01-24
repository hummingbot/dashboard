import logging
import math
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import pandas as pd
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient


class MongoDBClient:
    def __init__(
            self,
            debug_mode: bool = False,
            username: Optional[str] = None,
            password: Optional[str] = None,
            host: Optional[str] = None,
            port: Optional[str] = None,
            database: str = "mongodb"
    ):
        self.client = None
        self.db = None
        self.debug_mode = debug_mode
        load_dotenv()

        # Connection parameters with env fallbacks
        self.username = username or os.getenv('MONGO_INITDB_ROOT_USERNAME', "admin")
        self.password = password or os.getenv('MONGO_INITDB_ROOT_PASSWORD', "admin")
        self.host = host or os.getenv('MONGO_HOST', 'localhost')
        self.port = port or os.getenv('MONGO_PORT', '27017')
        self.database = database

    async def connect(self):
        """Connect to MongoDB using provided or environment variables."""
        connection_string = f"mongodb://{self.username}:{self.password}@{self.host}:{self.port}/?authSource=admin"
        try:
            self.client = AsyncIOMotorClient(
                connection_string,
                serverSelectionTimeoutMS=5000
            )
            self.db = self.client[self.database]
            await self.db.command('ping')
            logging.info(f"Successfully connected to MongoDB at {self.host}:{self.port}")

            # Create index on timestamp if it doesn't exist
            await self.db.pools.create_index('timestamp', unique=True)

            # If in debug mode, reset collections
            if self.debug_mode:
                await self.reset_collections()

        except Exception as e:
            print(f"Failed to connect to MongoDB: {str(e)}")
            raise

    async def reset_collections(self):
        """Reset all collections in the database."""
        try:
            result = await self.db.pools.delete_many({})
            print(f"Reset collections: Deleted {result.deleted_count} documents from pools collection")
        except Exception as e:
            print(f"Error resetting collections: {str(e)}")
            raise

    async def disconnect(self):
        """Disconnect from MongoDB."""
        if self.client:
            self.client.close()
            print("Disconnected from MongoDB")

    async def add_pools_data(self, trending_pools_df: pd.DataFrame, new_pools_df: pd.DataFrame,
                             filtered_trending_pools_df: pd.DataFrame, filtered_new_pools_df: pd.DataFrame):
        """
        Add all pools data to MongoDB in a single document with timestamp as primary key.
        """
        collection = self.db.pools
        timestamp = datetime.utcnow()

        document = {
            'timestamp': timestamp,
            'trending_pools': trending_pools_df.to_dict('records') if not trending_pools_df.empty else [],
            'filtered_trending_pools': filtered_trending_pools_df.to_dict(
                'records') if not filtered_trending_pools_df.empty else [],
            'new_pools': new_pools_df.to_dict('records') if not new_pools_df.empty else [],
            'filtered_new_pools': filtered_new_pools_df.to_dict('records') if not filtered_new_pools_df.empty else []
        }

        try:
            await collection.insert_one(document)
            print(f"Successfully inserted pools data for timestamp {timestamp}")

            # Verify counts
            print(f"Trending pools: {len(document['trending_pools'])}")
            print(f"Filtered trending pools: {len(document['filtered_trending_pools'])}")
            print(f"New pools: {len(document['new_pools'])}")
            print(f"Filtered new pools: {len(document['filtered_new_pools'])}")

        except Exception as e:
            print(f"Error inserting pools data: {str(e)}")
            raise

    async def get_pools_data(self, hours_ago: int = None) -> dict:
        """
        Get pools data from MongoDB.
        Args:
            hours_ago: If provided, only return data from the last N hours
        Returns:
            Dictionary containing DataFrames for each pool type
        """
        collection = self.db.pools
        query = {}

        if hours_ago is not None:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours_ago)
            query = {'timestamp': {'$gte': cutoff_time}}

        try:
            cursor = collection.find(query).sort('timestamp', -1)  # Sort by timestamp descending
            documents = await cursor.to_list(length=None)

            if not documents:
                print("No pools data found")
                return {
                    'trending_pools': pd.DataFrame(),
                    'filtered_trending_pools': pd.DataFrame(),
                    'new_pools': pd.DataFrame(),
                    'filtered_new_pools': pd.DataFrame(),
                    'timestamps': []
                }

            # Separate the data into different DataFrames
            result = {
                'trending_pools': pd.DataFrame(),
                'filtered_trending_pools': pd.DataFrame(),
                'new_pools': pd.DataFrame(),
                'filtered_new_pools': pd.DataFrame(),
                'timestamps': [doc['timestamp'] for doc in documents]
            }

            # Combine all documents into single DataFrames
            for key in ['trending_pools', 'filtered_trending_pools', 'new_pools', 'filtered_new_pools']:
                all_records = []
                for doc in documents:
                    records = doc[key]
                    for record in records:
                        record['timestamp'] = doc['timestamp']
                    all_records.extend(records)

                if all_records:
                    result[key] = pd.DataFrame(all_records)

            print(f"Retrieved data for {len(documents)} timestamps")
            for key, df in result.items():
                if isinstance(df, pd.DataFrame):
                    print(f"{key}: {len(df)} records")

            return result

        except Exception as e:
            print(f"Error retrieving pools data: {str(e)}")
            raise

    async def get_latest_pools_data(self) -> dict:
        """
        Get the most recent pools data entry.
        Returns:
            Dictionary containing DataFrames for each pool type from the latest entry
        """
        collection = self.db.pools

        try:
            document = await collection.find_one(sort=[('timestamp', -1)])

            if not document:
                print("No pools data found")
                return {
                    'trending_pools': pd.DataFrame(),
                    'filtered_trending_pools': pd.DataFrame(),
                    'new_pools': pd.DataFrame(),
                    'filtered_new_pools': pd.DataFrame(),
                    'timestamp': None
                }

            result = {
                'timestamp': document['timestamp'],
                'trending_pools': pd.DataFrame(document['trending_pools']),
                'filtered_trending_pools': pd.DataFrame(document['filtered_trending_pools']),
                'new_pools': pd.DataFrame(document['new_pools']),
                'filtered_new_pools': pd.DataFrame(document['filtered_new_pools'])
            }

            print(f"Retrieved latest data from {document['timestamp']}")
            for key, df in result.items():
                if isinstance(df, pd.DataFrame):
                    print(f"{key}: {len(df)} records")

            return result

        except Exception as e:
            print(f"Error retrieving latest pools data: {str(e)}")
            raise

    async def add_funding_rates_data(self, funding_rates: List[Dict[str, Any]]) -> None:
        """
        Add funding rates data to MongoDB.

        Args:
            funding_rates (List[Dict]): List of funding rate records with structure:
            {
                "index_price": float,
                "mark_price": float,
                "next_funding_utc_timestamp": int,
                "rate": float,
                "trading_pair": str,
                "connector_name": str,
                "timestamp": float
            }
        """
        try:
            if not funding_rates:
                logging.warning("No funding rates data to insert")
                return

            collection = self.db.funding_rates

            # Create indexes if they don't exist
            await collection.create_index([
                ("trading_pair", 1),
                ("connector_name", 1),
                ("next_funding_utc_timestamp", 1)
            ])

            # Insert the funding rates data
            result = await collection.insert_many(funding_rates)
            logging.info(f"Successfully inserted {len(result.inserted_ids)} funding rate records")

        except Exception as e:
            logging.error(f"Error adding funding rates data: {str(e)}")
            raise

    async def add_cointegration_results_data(self, cointegration_results: List[Dict[str, Any]]) -> None:
        """
        Add cointegration analysis results to MongoDB.

        Args:
            cointegration_results (List[Dict]): List of cointegration result records with structure:
            {
                'base': str,           # The pair to go long
                'quote': str,          # The pair to go short
                'grid_base': {
                    'start_price': float,  # Entry price for long
                    'end_price': float,    # Target price for long
                    'limit_price': float,  # Stop price for long
                    'beta': float          # Coint Sensibility
                },
                'grid_quote': {
                    'start_price': float,  # Entry price for short
                    'end_price': float,    # Target price for short
                    'limit_price': float,  # Stop price for short
                    'beta': float          # Coint Sensibility
                },
                'coint_value': float       # Average cointegration value
            }
        """
        try:
            if not cointegration_results:
                logging.warning("No cointegration results data to insert")
                return

            collection = self.db.cointegration_results

            # Create indexes if they don't exist
            await collection.create_index([
                ("base", 1),
                ("quote", 1)
            ])

            # Insert the cointegration results data
            result = await collection.insert_many(cointegration_results)
            logging.info(f"Successfully inserted {len(result.inserted_ids)} cointegration result records")

        except Exception as e:
            logging.error(f"Error adding cointegration results data: {str(e)}")
            raise

    async def get_cointegration_results(self, base: Optional[str] = None, quote: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Retrieve cointegration results from MongoDB with optional filtering by base and quote pairs.

        Args:
            base (str, optional): The base trading pair to filter by
            quote (str, optional): The quote trading pair to filter by

        Returns:
            List[Dict]: List of cointegration result records matching the criteria
        """
        try:
            collection = self.db.cointegration_results
            query = {}

            if base:
                query["base"] = base
            if quote:
                query["quote"] = quote

            cursor = collection.find(query)
            cointegration_results = await cursor.to_list(length=None)

            logging.info(f"Retrieved {len(cointegration_results)} cointegration result records")
            return cointegration_results

        except Exception as e:
            logging.error(f"Error retrieving cointegration results: {str(e)}")
            raise

    async def get_funding_rates(self, symbol: Optional[str] = None, start_time: Optional[datetime] = None,
                                end_time: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """
        Retrieve funding rates from MongoDB with optional filtering by symbol and time range.

        Args:
            symbol (str, optional): The trading pair symbol to filter by
            start_time (datetime, optional): Start of time range to fetch rates from
            end_time (datetime, optional): End of time range to fetch rates from

        Returns:
            List[Dict]: List of funding rate records matching the criteria
        """
        try:
            collection = self.db.funding_rates
            query = {}

            if symbol:
                query["symbol"] = symbol

            if start_time or end_time:
                query["timestamp"] = {}
                if start_time:
                    query["timestamp"]["$gte"] = start_time
                if end_time:
                    query["timestamp"]["$lte"] = end_time

            cursor = collection.find(query)
            funding_rates = await cursor.to_list(length=None)

            logging.info(f"Retrieved {len(funding_rates)} funding rate records")
            return funding_rates

        except Exception as e:
            logging.error(f"Error retrieving funding rates: {str(e)}")
            raise

    async def add_funding_rates_processed_data(self, processed_data: List[Dict[str, Any]]):
        """
        Add processed funding rates data to MongoDB with timestamp, pair1, pair2 and rate_difference.

        Args:
            processed_data (List[Dict]): List of dictionaries containing processed funding rate data
                                       with timestamp, pair1, pair2 and rate_difference fields
        """
        try:
            collection = self.db.funding_rates_processed

            # Create compound index on timestamp and pairs if it doesn't exist
            await collection.create_index([
                ("timestamp", 1),
                ("pair1", 1),
                ("pair2", 1)
            ])

            # Insert the processed funding rates data
            result = await collection.insert_many(processed_data)
            logging.info(f"Successfully inserted {len(result.inserted_ids)} processed funding rate records")

        except Exception as e:
            logging.error(f"Error adding processed funding rates data: {str(e)}")
            raise

    async def get_funding_rates_processed(self,
                                          pair1: Optional[str] = None,
                                          pair2: Optional[str] = None,
                                          start_time: Optional[datetime] = None,
                                          end_time: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """
        Retrieve processed funding rates from MongoDB with optional filtering by pairs and time range.

        Args:
            pair1 (str, optional): First trading pair to filter by
            pair2 (str, optional): Second trading pair to filter by
            start_time (datetime, optional): Start of time range to fetch rates from
            end_time (datetime, optional): End of time range to fetch rates from

        Returns:
            List[Dict]: List of processed funding rate records matching the criteria
        """
        try:
            collection = self.db.funding_rates_processed
            query = {}

            if pair1:
                query["pair1"] = pair1
            if pair2:
                query["pair2"] = pair2

            if start_time or end_time:
                query["timestamp"] = {}
                if start_time:
                    query["timestamp"]["$gte"] = start_time
                if end_time:
                    query["timestamp"]["$lte"] = end_time

            cursor = collection.find(query)
            processed_rates = await cursor.to_list(length=None)

            logging.info(f"Retrieved {len(processed_rates)} processed funding rate records")
            return processed_rates

        except Exception as e:
            logging.error(f"Error retrieving processed funding rates: {str(e)}")
            raise

    async def add_controller_config_data(self, processed_data: List[Dict[str, Any]]):
        try:
            collection = self.db.controller_configs

            # Create compound index on timestamp and pairs if it doesn't exist
            await collection.create_index([
                ("controller_name", 1),
                ("controller_type", 1),
                ("connector_name", 1)
            ])

            # Insert the processed funding rates data
            result = await collection.insert_many(processed_data)
            logging.info(f"Successfully inserted {len(result.inserted_ids)} processed funding rate records")

        except Exception as e:
            logging.error(f"Error adding controller config data: {str(e)}")
            raise

    async def get_controller_config_data(self,
                                         controller_name: str = None,
                                         controller_type: str = None,
                                         connector_name: str = None):
        collection = self.db.controller_configs
        query = {}

        if controller_name:
            query["controller_name"] = controller_name
        if controller_type:
            query["controller_type"] = controller_type
        if connector_name:
            query["connector_name"] = connector_name

        cursor = collection.find(query)
        controller_configs = await cursor.to_list(length=None)

        # Filter out configs with NaN in grid_config_base or grid_config_quote
        filtered_configs = [
            config for config in controller_configs
            if not any(
                math.isnan(config["config"]["grid_config_base"].get(field, float('inf'))) or
                math.isnan(config["config"]["grid_config_quote"].get(field, float('inf')))
                for field in ["end_price", "start_price", "limit_price"]
            )
        ]

        logging.info(f"Retrieved {len(filtered_configs)} filtered controller config records")
        return filtered_configs
