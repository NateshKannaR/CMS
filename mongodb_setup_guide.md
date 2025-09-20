# MongoDB Atlas Setup Guide

## Step 1: Network Access Configuration
1. In MongoDB Atlas, go to "Network Access" in the left sidebar
2. Click "Add IP Address"
3. Select "Allow Access from Anywhere" (0.0.0.0/0) for testing
4. Click "Confirm"

## Step 2: Database User Configuration
1. Go to "Database Access" in the left sidebar
2. Click "Add New Database User"
3. Username: Natesh
4. Password: Natesh
5. Database User Privileges: "Read and write to any database"
6. Click "Add User"

## Step 3: Get Connection String
1. Go to "Clusters" in the left sidebar
2. Click "Connect" on your cluster
3. Select "Connect your application"
4. Choose "Python" and version "3.6 or later"
5. Copy the connection string

## Step 4: Test Connection
The connection string should look like:
mongodb+srv://Natesh:<password>@cluster0.wwp3oig.mongodb.net/?retryWrites=true&w=majority

Replace <password> with your actual password.