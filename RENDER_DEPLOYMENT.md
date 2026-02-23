# Render Deployment Guide

## Fixed Issues
✅ **Migration Error Fixed**: Added missing `formatter_generic` configuration to `alembic.ini`

## Quick Deploy to Render

### 1. Push to GitHub
```bash
git add .
git commit -m "Fix alembic logging configuration for Render deployment"
git push origin main
```

### 2. Deploy on Render
1. Go to [render.com](https://render.com)
2. Connect your GitHub account
3. Select this repository
4. Render will automatically detect the `render.yaml` configuration
5. Click "Deploy Web Service"

### 3. Environment Variables
The following environment variables are automatically configured:
- `DATABASE_URL`: Connected to PostgreSQL database
- `JWT_SECRET_KEY`: Auto-generated secure key
- `FLASK_ENV`: Set to production
- `PORT`: Set to 5000

### 4. Manual Environment Variables (if needed)
Add these in Render dashboard if not auto-configured:
- `STRIPE_SECRET_KEY`: Your Stripe secret key
- `STRIPE_WEBHOOK_SECRET`: Stripe webhook secret
- `OPENAI_API_KEY`: OpenAI API key (for AI features)
- `REDIS_URL`: Redis connection string (if using external Redis)

## What's Included

### Web Service Configuration
- **Runtime**: Python 3
- **Build**: Installs requirements.txt
- **Start**: Runs `start_render.py` (handles migrations automatically)
- **Health Check**: `/health` endpoint
- **Plan**: Free tier (upgrade as needed)

### Database Configuration
- **Type**: PostgreSQL
- **Plan**: Free tier
- **Name**: legalize-db
- **Auto-migration**: Handled by startup script

## Startup Process
The `start_render.py` script handles:
1. Database connection check
2. Automatic Alembic migrations
3. Initial data creation (if needed)
4. Gunicorn server startup

## Post-Deployment
1. Check deployment logs in Render dashboard
2. Test API endpoints
3. Configure additional environment variables for payments/AI features
4. Set up custom domain (optional)

## Troubleshooting

### Migration Issues
If migrations fail:
1. Check the deployment logs
2. Verify `DATABASE_URL` is correctly set
3. Ensure database is accessible

### Health Check Failures
1. Verify the `/health` endpoint exists in your Flask app
2. Check if the app is binding to the correct PORT (5000)

### Database Connection
1. Ensure PostgreSQL is running
2. Check connection string format
3. Verify database user permissions

## Scaling
- **Web Service**: Upgrade plan for more CPU/memory
- **Database**: Upgrade plan for better performance
- **Redis**: Add Redis service for background jobs/caching

## Monitoring
- Render provides built-in monitoring
- Check logs in dashboard
- Set up alerts for downtime
