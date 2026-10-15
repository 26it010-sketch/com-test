FROM nginx:alpine

# Copy the Nginx configuration
COPY meena.conf /etc/nginx/conf.d/default.conf

# Copy the built React frontend
COPY dist/ /usr/share/nginx/html/
