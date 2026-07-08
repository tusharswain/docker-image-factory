"""
Dockerfile Generator Module
Generates optimized multi-stage Dockerfiles for various languages and frameworks
"""

import os
import logging
from pathlib import Path
from typing import Dict, Optional


class DockerfileGenerator:
    """Generate optimized Dockerfiles for different languages"""
    
    def __init__(self, config: Dict):
        """Initialize the Dockerfile generator"""
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.templates_dir = Path(__file__).parent.parent / 'templates'
    
    def generate(self, language: str, app_path: str, base_image: str = None, 
                 custom_args: Dict = None) -> Optional[str]:
        """
        Generate a Dockerfile for the specified language
        
        Args:
            language: Programming language/framework
            app_path: Path to application source code
            base_image: Custom base image (optional)
            custom_args: Additional custom arguments
        
        Returns:
            str: Path to generated Dockerfile
        """
        try:
            self.logger.info(f"Generating Dockerfile for {language}")
            
            # Get template for language
            template = self._get_template(language, base_image, custom_args or {})
            
            if not template:
                self.logger.error(f"No template found for language: {language}")
                return None
            
            # Write Dockerfile to app path
            dockerfile_path = Path(app_path) / 'Dockerfile'
            
            with open(dockerfile_path, 'w') as f:
                f.write(template)
            
            self.logger.info(f"Dockerfile generated at {dockerfile_path}")
            return str(dockerfile_path)
            
        except Exception as e:
            self.logger.error(f"Error generating Dockerfile: {str(e)}")
            return None
    
    def _get_template(self, language: str, base_image: str = None, 
                     custom_args: Dict = None) -> Optional[str]:
        """Get Dockerfile template for the specified language"""
        templates = {
            'python': self._python_template,
            'java': self._java_template,
            'node': self._node_template,
            'groovy': self._groovy_template,
            'robot': self._robot_template,
            'go': self._go_template,
            'dotnet': self._dotnet_template
        }
        
        template_func = templates.get(language.lower())
        if template_func:
            return template_func(base_image, custom_args or {})
        
        return None
    
    def _python_template(self, base_image: str = None, custom_args: Dict = None) -> str:
        """Generate Python Dockerfile template"""
        python_version = custom_args.get('python_version', '3.11-slim')
        requirements_file = custom_args.get('requirements_file', 'requirements.txt')
        port = custom_args.get('port', '8000')
        
        base = base_image or f'python:{python_version}'
        
        # Extract major.minor version for the COPY --from path (e.g. "3.11-slim" -> "3.11")
        raw = python_version.split('-')[0]  # e.g. "3.11"
        parts = raw.split('.')
        py_dir = f"{parts[0]}.{parts[1]}" if len(parts) >= 2 else "3.11"
        
        return f"""# Multi-stage Python Dockerfile
FROM {base} AS builder

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    g++ \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY {requirements_file} .
RUN pip install --no-cache-dir -r {requirements_file}

# Final stage
FROM {base}

WORKDIR /app

# Copy installed dependencies from builder
COPY --from=builder /usr/local/lib/python{py_dir}/site-packages /usr/local/lib/python{py_dir}/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE {port}

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:{port}/health')" || exit 1

# Run application
CMD ["python", "main.py"]
"""
    
    def _java_template(self, base_image: str = None, custom_args: Dict = None) -> str:
        """Generate Java Dockerfile template"""
        java_version = custom_args.get('java_version', '17')
        build_tool = custom_args.get('build_tool', 'maven')  # maven or gradle
        port = custom_args.get('port', '8080')
        
        if build_tool == 'gradle':
            builder_base = base_image or f'gradle:8.5-jdk{java_version}'
            runtime_base = base_image or f'eclipse-temurin:{java_version}-jre'
        else:
            builder_base = base_image or f'maven:3.9-eclipse-temurin-{java_version}'
            runtime_base = base_image or f'eclipse-temurin:{java_version}-jre'
        
        if build_tool == 'gradle':
            return f"""# Multi-stage Java Dockerfile (Gradle)
FROM {builder_base} AS builder

WORKDIR /app

# Copy Gradle files
COPY build.gradle settings.gradle ./
COPY gradle ./gradle

# Download dependencies
RUN gradle dependencies --no-daemon

# Copy source code
COPY src ./src

# Build application
RUN gradle build --no-daemon

# Final stage
FROM {runtime_base}

WORKDIR /app

# Copy JAR from builder
COPY --from=builder /app/build/libs/*.jar app.jar

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE {port}

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:{port}/actuator/health || exit 1

# Run application
CMD ["java", "-jar", "app.jar"]
"""
        else:
            return f"""# Multi-stage Java Dockerfile (Maven)
FROM {builder_base} AS builder

WORKDIR /app

# Copy Maven files
COPY pom.xml .

# Download dependencies
RUN mvn dependency:go-offline -B

# Copy source code
COPY src ./src

# Build application
RUN mvn clean package -DskipTests

# Final stage
FROM {runtime_base}

WORKDIR /app

# Copy JAR from builder
COPY --from=builder /app/target/*.jar app.jar

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE {port}

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:{port}/actuator/health || exit 1

# Run application
CMD ["java", "-jar", "app.jar"]
"""
    
    def _node_template(self, base_image: str = None, custom_args: Dict = None) -> str:
        """Generate Node.js Dockerfile template"""
        node_version = custom_args.get('node_version', '18-alpine')
        port = custom_args.get('port', '3000')
        
        base = base_image or f'node:{node_version}'
        
        return f"""# Multi-stage Node.js Dockerfile
FROM {base} AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy application code
COPY . .

# Build application (if needed)
RUN npm run build || true

# Final stage
FROM {base}

WORKDIR /app

# Copy dependencies and built files from builder
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/package*.json ./

# Create non-root user
RUN addgroup -g 1001 -S nodejs && \\
    adduser -S nodejs -u 1001 && \\
    chown -R nodejs:nodejs /app
USER nodejs

# Expose port
EXPOSE {port}

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD node -e "require('http').get('http://localhost:{port}/health', (r) => {{process.exit(r.statusCode === 200 ? 0 : 1)}})" || exit 1

# Run application
CMD ["node", "dist/index.js"]
"""
    
    def _groovy_template(self, base_image: str = None, custom_args: Dict = None) -> str:
        """Generate Groovy Dockerfile template"""
        groovy_version = custom_args.get('groovy_version', '4.0')
        jdk_version = custom_args.get('jdk_version', '17')
        port = custom_args.get('port', '8080')
        
        builder_base = base_image or f'groovy:{groovy_version}-jdk{jdk_version}'
        runtime_base = base_image or f'eclipse-temurin:{jdk_version}-jre'
        
        return f"""# Multi-stage Groovy Dockerfile
FROM {builder_base} AS builder

WORKDIR /app

# Copy Groovy source files
COPY src ./src
COPY build.gradle settings.gradle ./

# Build application
RUN gradle build --no-daemon

# Final stage
FROM {runtime_base}

WORKDIR /app

# Copy JAR from builder
COPY --from=builder /app/build/libs/*.jar app.jar

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE {port}

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:{port}/health || exit 1

# Run application
CMD ["java", "-jar", "app.jar"]
"""
    
    def _robot_template(self, base_image: str = None, custom_args: Dict = None) -> str:
        """Generate Robot Framework Dockerfile template"""
        python_version = custom_args.get('python_version', '3.11-slim')
        
        base = base_image or f'python:{python_version}'
        
        # Extract major.minor version for the COPY --from path
        raw = python_version.split('-')[0]
        parts = raw.split('.')
        py_dir = f"{parts[0]}.{parts[1]}" if len(parts) >= 2 else "3.11"
        
        return f"""# Multi-stage Robot Framework Dockerfile
FROM {base} AS builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    g++ \\
    xvfb \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Final stage
FROM {base}

WORKDIR /app

# Copy installed dependencies from builder
COPY --from=builder /usr/local/lib/python{py_dir}/site-packages /usr/local/lib/python{py_dir}/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy Robot Framework tests
COPY tests ./tests
COPY resources ./resources

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Run Robot Framework tests
CMD ["robot", "--outputdir", "/app/results", "/app/tests"]
"""
    
    def _go_template(self, base_image: str = None, custom_args: Dict = None) -> str:
        """Generate Go Dockerfile template"""
        go_version = custom_args.get('go_version', '1.21-alpine')
        port = custom_args.get('port', '8080')
        
        builder_base = base_image or f'golang:{go_version}'
        runtime_base = base_image or 'alpine:latest'
        
        return f"""# Multi-stage Go Dockerfile
FROM {builder_base} AS builder

WORKDIR /app

# Copy go mod files
COPY go.mod go.sum ./

# Download dependencies
RUN go mod download

# Copy source code
COPY . .

# Build application
RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o main .

# Final stage
FROM {runtime_base}

WORKDIR /app

# Install ca-certificates for HTTPS
RUN apk --no-cache add ca-certificates

# Copy binary from builder
COPY --from=builder /app/main .

# Create non-root user
RUN addgroup -g 1000 appuser && \\
    adduser -D -u 1000 -G appuser appuser && \\
    chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE {port}

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD wget --no-verbose --tries=1 --spider http://localhost:{port}/health || exit 1

# Run application
CMD ["./main"]
"""
    
    def _dotnet_template(self, base_image: str = None, custom_args: Dict = None) -> str:
        """Generate .NET Dockerfile template"""
        dotnet_version = custom_args.get('dotnet_version', '7.0')
        port = custom_args.get('port', '8080')
        
        builder_base = base_image or f'mcr.microsoft.com/dotnet/sdk:{dotnet_version}'
        runtime_base = base_image or f'mcr.microsoft.com/dotnet/aspnet:{dotnet_version}'
        
        return f"""# Multi-stage .NET Dockerfile
FROM {builder_base} AS builder

WORKDIR /src

# Copy project files
COPY ["*.csproj", "./"]
RUN dotnet restore

# Copy source code
COPY . .

# Build application
WORKDIR "/src"
RUN dotnet build -c Release -o /app/build

# Publish application
FROM builder AS publish
RUN dotnet publish "src.csproj" -c Release -o /app/publish /p:UseAppHost=false

# Final stage
FROM {runtime_base} AS final
WORKDIR /app

# Copy published application
COPY --from=publish /app/publish .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE {port}

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:{port}/health || exit 1

# Run application
ENTRYPOINT ["dotnet", "src.dll"]
"""
