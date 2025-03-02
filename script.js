// ConvoBot.js - Main JavaScript file for the ConvoBot website

document.addEventListener('DOMContentLoaded', function() {
    // Mobile navigation toggle
    setupMobileNav();
    
    // Animated typing effect for the demo
    initTypingAnimation();
    
    // Interactive demo chat
    setupInteractiveDemo();
    
    // Scroll animations
    setupScrollAnimations();
    
    // Feature card hover effects
    setupFeatureCards();
    
    // Smooth scrolling for navigation links
    setupSmoothScroll();
});

// Mobile navigation functionality
function setupMobileNav() {
    const hamburger = document.createElement('div');
    hamburger.className = 'hamburger-menu';
    hamburger.innerHTML = '<span></span><span></span><span></span>';
    document.querySelector('.navbar').appendChild(hamburger);
    
    hamburger.addEventListener('click', function() {
        const navLinks = document.querySelector('.nav-links');
        navLinks.classList.toggle('active');
        hamburger.classList.toggle('active');
    });
}

// Typing animation effect for the hero section
function initTypingAnimation() {
    const headingText = document.querySelector('.hero h1').textContent;
    const headingElement = document.querySelector('.hero h1');
    
    // Clear the heading and prepare for animation
    headingElement.textContent = '';
    
    let i = 0;
    const typeWriter = () => {
        if (i < headingText.length) {
            headingElement.textContent += headingText.charAt(i);
            i++;
            setTimeout(typeWriter, 100);
        }
    };
    
    // Add a slight delay before starting the animation
    setTimeout(typeWriter, 500);
}

// Interactive chat demo functionality
function setupInteractiveDemo() {
    const chatContainer = document.querySelector('.chat-container');
    const demoResponses = [
        "I can help with that! What kind of schedule are you looking to create?",
        "Great! I've added those meetings to your calendar. Would you like me to set reminders?",
        "Based on your schedule, I've allocated focused work time for your project on Tuesday and Wednesday. How does that sound?",
        "Perfect! Your schedule is now organized. Is there anything else you'd like help with today?"
    ];
    
    const userPrompts = [
        "I need help planning my week",
        "Yes, please set reminders 15 minutes before each meeting",
        "That sounds perfect, thank you!",
        "Can you also help me draft an email about the project?"
    ];
    
    let currentResponse = 0;
    
    // Add click event for the demo container
    document.querySelector('.demo-container').addEventListener('click', function() {
        if (currentResponse >= demoResponses.length) {
            // Reset the demo
            while (chatContainer.children.length > 5) {
                chatContainer.removeChild(chatContainer.lastChild);
            }
            currentResponse = 0;
            return;
        }
        
        // Add user message
        const userMessage = createMessageElement('user', userPrompts[currentResponse]);
        chatContainer.appendChild(userMessage);
        
        // Scroll to bottom
        chatContainer.scrollTop = chatContainer.scrollHeight;
        
        // Add bot response after a delay
        setTimeout(() => {
            const botMessage = createMessageElement('bot', demoResponses[currentResponse]);
            chatContainer.appendChild(botMessage);
            
            // Scroll to bottom
            chatContainer.scrollTop = chatContainer.scrollHeight;
            
            currentResponse++;
        }, 1000);
    });
}

// Helper function to create message elements
function createMessageElement(type, text) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}`;
    
    const avatar = document.createElement('div');
    avatar.className = 'avatar';
    avatar.textContent = type === 'bot' ? 'CB' : 'U';
    
    const content = document.createElement('div');
    content.className = 'message-content';
    content.textContent = text;
    
    messageDiv.appendChild(avatar);
    messageDiv.appendChild(content);
    
    return messageDiv;
}

// Scroll animations for sections
function setupScrollAnimations() {
    const elements = document.querySelectorAll('.feature-card, .step-card, .section-title');
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate');
                observer.unobserve(entry.target);
            }
        });
    }, {
        threshold: 0.1
    });
    
    elements.forEach(element => {
        element.style.opacity = '0';
        element.style.transform = 'translateY(20px)';
        element.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
        observer.observe(element);
    });
    
    // Add CSS class for animated elements
    const style = document.createElement('style');
    style.textContent = `
        .animate {
            opacity: 1 !important;
            transform: translateY(0) !important;
        }
    `;
    document.head.appendChild(style);
}

// Feature card hover interactions
function setupFeatureCards() {
    const featureCards = document.querySelectorAll('.feature-card');
    
    featureCards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            const icon = this.querySelector('.feature-icon');
            icon.style.transform = 'scale(1.2) rotate(5deg)';
            icon.style.transition = 'transform 0.3s ease';
        });
        
        card.addEventListener('mouseleave', function() {
            const icon = this.querySelector('.feature-icon');
            icon.style.transform = 'scale(1) rotate(0deg)';
        });
    });
}

// Smooth scrolling for navigation
function setupSmoothScroll() {
    const navLinks = document.querySelectorAll('.nav-links a[href^="#"]');
    
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            
            const targetId = this.getAttribute('href');
            if (targetId === '#') return;
            
            const targetElement = document.querySelector(targetId);
            if (targetElement) {
                // Close mobile menu if open
                document.querySelector('.nav-links').classList.remove('active');
                document.querySelector('.hamburger-menu')?.classList.remove('active');
                
                // Scroll to the element
                window.scrollTo({
                    top: targetElement.offsetTop - 80,
                    behavior: 'smooth'
                });
            }
        });
    });
}

// Track scroll position for sticky header effects
window.addEventListener('scroll', function() {
    const header = document.querySelector('header');
    if (window.scrollY > 100) {
        header.classList.add('scrolled');
    } else {
        header.classList.remove('scrolled');
    }
});

// Add additional styles for scrolled header
const headerStyle = document.createElement('style');
headerStyle.textContent = `
    header.scrolled {
        box-shadow: 0 5px 20px rgba(0, 0, 0, 0.15);
    }
    header.scrolled .navbar {
        padding: 15px 0;
    }
    .navbar {
        transition: padding 0.3s ease;
    }
    
    /* Mobile Navigation Styles */
    .hamburger-menu {
        display: none;
        cursor: pointer;
        width: 30px;
        height: 20px;
        position: relative;
        z-index: 101;
    }
    .hamburger-menu span {
        display: block;
        width: 100%;
        height: 3px;
        background-color: var(--dark);
        position: absolute;
        transition: all 0.3s ease;
    }
    .hamburger-menu span:nth-child(1) {
        top: 0;
    }
    .hamburger-menu span:nth-child(2) {
        top: 8px;
    }
    .hamburger-menu span:nth-child(3) {
        top: 16px;
    }
    .hamburger-menu.active span:nth-child(1) {
        transform: rotate(45deg);
        top: 8px;
    }
    .hamburger-menu.active span:nth-child(2) {
        opacity: 0;
    }
    .hamburger-menu.active span:nth-child(3) {
        transform: rotate(-45deg);
        top: 8px;
    }
    
    @media (max-width: 768px) {
        .hamburger-menu {
            display: block;
        }
        .nav-links {
            position: fixed;
            top: 0;
            right: -100%;
            width: 250px;
            height: 100vh;
            background-color: white;
            display: flex;
            flex-direction: column;
            justify-content: flex-start;
            align-items: flex-start;
            padding: 80px 20px 20px;
            transition: right 0.3s ease;
            box-shadow: -5px 0 15px rgba(0, 0, 0, 0.1);
            z-index: 100;
        }
        .nav-links.active {
            right: 0;
        }
        .nav-links li {
            margin: 15px 0;
        }
    }
`;
document.head.appendChild(headerStyle);