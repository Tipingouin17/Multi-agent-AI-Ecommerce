# Design System & UI/UX Requirements
## Multi-Agent E-commerce Platform

### Overview
This document defines the comprehensive design system requirements for creating world-class, consistent user interfaces across all components of the multi-agent e-commerce platform. The goal is to deliver a cohesive, professional software experience that feels like a unified product.

---

## 🎨 Design System Foundation

### Color Palette
**Primary Colors:**
- **Primary Blue**: `#2563eb` (Modern, trustworthy, professional)
- **Primary Blue Light**: `#3b82f6`
- **Primary Blue Dark**: `#1d4ed8`

**Secondary Colors:**
- **Success Green**: `#10b981` (Confirmations, success states)
- **Warning Orange**: `#f59e0b` (Alerts, pending states)
- **Error Red**: `#ef4444` (Errors, critical alerts)
- **Info Purple**: `#8b5cf6` (Information, insights)

**Neutral Colors:**
- **Gray 50**: `#f9fafb` (Background, subtle elements)
- **Gray 100**: `#f3f4f6` (Light backgrounds)
- **Gray 200**: `#e5e7eb` (Borders, dividers)
- **Gray 300**: `#d1d5db` (Disabled states)
- **Gray 400**: `#9ca3af` (Placeholder text)
- **Gray 500**: `#6b7280` (Secondary text)
- **Gray 600**: `#4b5563` (Primary text)
- **Gray 700**: `#374151` (Headings)
- **Gray 800**: `#1f2937` (Dark text)
- **Gray 900**: `#111827` (Darkest text)

**Background Colors:**
- **White**: `#ffffff` (Primary background)
- **Light Gray**: `#f8fafc` (Secondary background)
- **Dark**: `#0f172a` (Dark mode primary)

### Typography
**Font Family:**
- **Primary**: `Inter, system-ui, -apple-system, sans-serif`
- **Monospace**: `'JetBrains Mono', 'Fira Code', monospace` (for code, IDs)

**Font Scales:**
- **Display**: `text-4xl` (36px) - Page titles, hero text
- **Heading 1**: `text-3xl` (30px) - Section headers
- **Heading 2**: `text-2xl` (24px) - Subsection headers
- **Heading 3**: `text-xl` (20px) - Card titles
- **Body Large**: `text-lg` (18px) - Important body text
- **Body**: `text-base` (16px) - Default body text
- **Body Small**: `text-sm` (14px) - Secondary text
- **Caption**: `text-xs` (12px) - Labels, captions

**Font Weights:**
- **Light**: `font-light` (300)
- **Regular**: `font-normal` (400)
- **Medium**: `font-medium` (500)
- **Semibold**: `font-semibold` (600)
- **Bold**: `font-bold` (700)

### Spacing System
**Consistent spacing scale using Tailwind CSS:**
- **xs**: `0.25rem` (4px)
- **sm**: `0.5rem` (8px)
- **md**: `1rem` (16px)
- **lg**: `1.5rem` (24px)
- **xl**: `2rem` (32px)
- **2xl**: `3rem` (48px)
- **3xl**: `4rem` (64px)

### Border Radius
- **Small**: `rounded-sm` (2px) - Small elements
- **Default**: `rounded` (4px) - Buttons, inputs
- **Medium**: `rounded-md` (6px) - Cards, containers
- **Large**: `rounded-lg` (8px) - Modals, panels
- **Extra Large**: `rounded-xl` (12px) - Hero sections
- **Full**: `rounded-full` - Avatars, badges

### Shadows
- **Small**: `shadow-sm` - Subtle elevation
- **Default**: `shadow` - Standard cards
- **Medium**: `shadow-md` - Elevated cards
- **Large**: `shadow-lg` - Modals, dropdowns
- **Extra Large**: `shadow-xl` - Overlays

---

## 🧩 Component Library

### Core Components

#### 1. **Buttons**
**Primary Button:**
```css
bg-blue-600 hover:bg-blue-700 text-white font-medium px-4 py-2 rounded-md
transition-colors duration-200 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2
```

**Secondary Button:**
```css
bg-gray-100 hover:bg-gray-200 text-gray-700 font-medium px-4 py-2 rounded-md
transition-colors duration-200 focus:ring-2 focus:ring-gray-500 focus:ring-offset-2
```

**Danger Button:**
```css
bg-red-600 hover:bg-red-700 text-white font-medium px-4 py-2 rounded-md
transition-colors duration-200 focus:ring-2 focus:ring-red-500 focus:ring-offset-2
```

#### 2. **Input Fields**
**Standard Input:**
```css
border border-gray-300 rounded-md px-3 py-2 text-gray-900 placeholder-gray-400
focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-colors duration-200
```

**Error State:**
```css
border-red-300 focus:border-red-500 focus:ring-red-500
```

#### 3. **Cards**
**Standard Card:**
```css
bg-white rounded-lg shadow border border-gray-200 p-6
```

**Elevated Card:**
```css
bg-white rounded-lg shadow-md border border-gray-200 p-6 hover:shadow-lg
transition-shadow duration-200
```

#### 4. **Status Badges**
**Success Badge:**
```css
bg-green-100 text-green-800 px-2 py-1 rounded-full text-xs font-medium
```

**Warning Badge:**
```css
bg-yellow-100 text-yellow-800 px-2 py-1 rounded-full text-xs font-medium
```

**Error Badge:**
```css
bg-red-100 text-red-800 px-2 py-1 rounded-full text-xs font-medium
```

#### 5. **Navigation**
**Sidebar Navigation:**
- Consistent width: `w-64` (256px)
- Background: `bg-gray-900`
- Text: `text-gray-300`
- Active state: `bg-blue-600 text-white`
- Hover state: `hover:bg-gray-800`

**Top Navigation:**
- Height: `h-16` (64px)
- Background: `bg-white border-b border-gray-200`
- Shadow: `shadow-sm`

---

## 📱 Interface Specifications

### 1. **Admin Dashboard Interface**
**Layout Structure:**
- **Sidebar Navigation**: Fixed left sidebar with agent status, system overview
- **Main Content Area**: Dynamic content with consistent padding
- **Header Bar**: Breadcrumbs, user profile, notifications
- **Footer**: System status, version info

**Key Sections:**
- **System Overview**: Real-time metrics, agent health status
- **Agent Management**: Individual agent controls and monitoring
- **Error Management**: AI recommendations, error logs, resolution tracking
- **Analytics Dashboard**: Performance metrics, trends, insights
- **Configuration**: System settings, API credentials, webhooks

### 2. **Merchant Interface**
**Layout Structure:**
- **Top Navigation**: Logo, main menu, account dropdown
- **Content Area**: Product management, order tracking, analytics
- **Action Panels**: Quick actions, notifications, help

**Key Sections:**
- **Product Catalog**: Inventory management, listing creation
- **Order Management**: Order tracking, fulfillment, returns
- **Marketplace Integration**: Channel management, sync status
- **Analytics**: Sales performance, inventory insights
- **Settings**: Store configuration, API settings

### 3. **Customer Interface**
**Layout Structure:**
- **Header**: Logo, search, cart, account
- **Main Content**: Product browsing, order tracking
- **Footer**: Links, support, company info

**Key Sections:**
- **Product Discovery**: Search, categories, recommendations
- **Order Tracking**: Real-time status, delivery updates
- **Account Management**: Profile, addresses, preferences
- **Support**: Chat interface, help center, contact

---

## 🎯 Interaction Design Principles

### Animation & Transitions
**Standard Durations:**
- **Fast**: `150ms` - Hover states, focus changes
- **Standard**: `200ms` - Button clicks, state changes
- **Slow**: `300ms` - Page transitions, modal appearances

**Easing Functions:**
- **Standard**: `ease-in-out` - Most transitions
- **Entrance**: `ease-out` - Elements appearing
- **Exit**: `ease-in` - Elements disappearing

### Micro-interactions
1. **Loading States**: Skeleton screens, progress indicators
2. **Hover Effects**: Subtle elevation, color changes
3. **Focus States**: Clear ring indicators, accessibility compliance
4. **Success Feedback**: Checkmarks, color changes, notifications
5. **Error Handling**: Inline validation, clear error messages

### Responsive Design
**Breakpoints:**
- **Mobile**: `< 640px`
- **Tablet**: `640px - 1024px`
- **Desktop**: `> 1024px`
- **Large Desktop**: `> 1280px`

**Mobile-First Approach:**
- Start with mobile design
- Progressive enhancement for larger screens
- Touch-friendly interface elements (minimum 44px touch targets)

---

## 📊 Data Visualization Standards

### Charts & Graphs
**Color Scheme for Data:**
- **Primary Data**: Blue gradient (`#2563eb` to `#3b82f6`)
- **Secondary Data**: Gray gradient (`#6b7280` to `#9ca3af`)
- **Success Metrics**: Green (`#10b981`)
- **Warning Metrics**: Orange (`#f59e0b`)
- **Error Metrics**: Red (`#ef4444`)

**Chart Types:**
- **Line Charts**: Trends over time
- **Bar Charts**: Comparisons, categories
- **Pie Charts**: Proportions (use sparingly)
- **Area Charts**: Volume over time
- **Heatmaps**: Performance matrices

### Tables
**Standard Table Styling:**
```css
bg-white shadow rounded-lg overflow-hidden
thead: bg-gray-50 text-gray-700 font-medium
tbody: divide-y divide-gray-200
rows: hover:bg-gray-50 transition-colors duration-150
```

---

## 🔧 Technical Implementation

### CSS Framework
**Primary**: Tailwind CSS with custom configuration
**Component Library**: Headless UI + custom components
**Icons**: Lucide React (consistent icon family)
**Charts**: Recharts with custom styling

### React Component Structure
```
components/
├── ui/                 # Base UI components
│   ├── Button.tsx
│   ├── Input.tsx
│   ├── Card.tsx
│   ├── Badge.tsx
│   └── ...
├── layout/            # Layout components
│   ├── Sidebar.tsx
│   ├── Header.tsx
│   ├── Navigation.tsx
│   └── ...
├── charts/            # Data visualization
│   ├── LineChart.tsx
│   ├── BarChart.tsx
│   └── ...
└── features/          # Feature-specific components
    ├── AgentStatus.tsx
    ├── OrderTable.tsx
    └── ...
```

### State Management
- **Global State**: Zustand for agent status, user session
- **Server State**: React Query for API data
- **Form State**: React Hook Form for form management

---

## ✅ Quality Assurance

### Accessibility (WCAG 2.1 AA)
- **Color Contrast**: Minimum 4.5:1 ratio for normal text
- **Keyboard Navigation**: Full keyboard accessibility
- **Screen Readers**: Proper ARIA labels and semantic HTML
- **Focus Management**: Clear focus indicators

### Performance Standards
- **First Contentful Paint**: < 1.5s
- **Largest Contentful Paint**: < 2.5s
- **Cumulative Layout Shift**: < 0.1
- **First Input Delay**: < 100ms

### Browser Support
- **Modern Browsers**: Chrome 90+, Firefox 88+, Safari 14+, Edge 90+
- **Mobile**: iOS Safari 14+, Chrome Mobile 90+

---

## 📋 Implementation Checklist

### Phase 1: Design System Setup
- [ ] Configure Tailwind CSS with custom theme
- [ ] Create base UI component library
- [ ] Implement design tokens
- [ ] Set up icon system

### Phase 2: Layout Components
- [ ] Build responsive navigation components
- [ ] Create layout templates for each interface type
- [ ] Implement responsive grid system
- [ ] Add animation utilities

### Phase 3: Feature Components
- [ ] Agent status and monitoring components
- [ ] Data visualization components
- [ ] Form and input components
- [ ] Table and list components

### Phase 4: Interface Assembly
- [ ] Admin dashboard interface
- [ ] Merchant interface
- [ ] Customer interface
- [ ] Mobile responsive versions

### Phase 5: Polish & Testing
- [ ] Accessibility audit and fixes
- [ ] Performance optimization
- [ ] Cross-browser testing
- [ ] User experience testing

---

## 🎨 Visual Examples

### Color Usage Guidelines
- **Primary Actions**: Blue (`#2563eb`)
- **Success States**: Green (`#10b981`)
- **Warnings**: Orange (`#f59e0b`)
- **Errors**: Red (`#ef4444`)
- **Information**: Purple (`#8b5cf6`)
- **Neutral**: Gray scale for text and backgrounds

### Component Hierarchy
1. **Page Level**: Large headings, primary actions
2. **Section Level**: Medium headings, secondary actions
3. **Component Level**: Small headings, tertiary actions
4. **Element Level**: Labels, captions, micro-copy

This design system ensures that every interface component feels like part of a cohesive, world-class software platform while maintaining consistency, accessibility, and professional polish across all user touchpoints.


---

## 📱 Responsive Design Requirements
## Mobile-First & Cross-Device Excellence

### Overview
Our multi-agent e-commerce platform MUST deliver exceptional user experiences across all devices, with particular focus on mobile phones and laptops. We follow a mobile-first approach, progressively enhancing for larger screens.

---

## 🎯 Device-Specific Design Strategy

### Mobile Phone Optimization (320px - 767px)
**Primary Focus**: Touch-first interaction, thumb-friendly navigation, simplified layouts

**Key Requirements:**
- **Minimum Touch Target**: 44px × 44px (Apple HIG standard)
- **Thumb Zone Navigation**: Critical actions within easy thumb reach
- **Single Column Layouts**: Avoid complex multi-column arrangements
- **Simplified Navigation**: Collapsible menus, bottom navigation bars
- **Readable Typography**: Minimum 16px font size to prevent zoom
- **Fast Loading**: Optimized images and minimal JavaScript

**Mobile-Specific Components:**
```css
/* Mobile Navigation */
.mobile-nav {
  position: fixed;
  bottom: 0;
  width: 100%;
  height: 60px;
  background: white;
  border-top: 1px solid #e5e7eb;
  display: flex;
  justify-content: space-around;
  align-items: center;
}

/* Mobile Touch Targets */
.touch-target {
  min-height: 44px;
  min-width: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* Mobile Cards */
.mobile-card {
  margin: 8px;
  padding: 16px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}
```

### Tablet Optimization (768px - 1023px)
**Primary Focus**: Hybrid touch/mouse interaction, efficient space utilization

**Key Requirements:**
- **Adaptive Layouts**: 2-column layouts where appropriate
- **Touch-Friendly**: Maintain 44px touch targets
- **Sidebar Navigation**: Collapsible sidebars for better space usage
- **Modal Optimization**: Larger modals with better content organization
- **Gesture Support**: Swipe navigation where applicable

### Laptop/Desktop Optimization (1024px+)
**Primary Focus**: Mouse/keyboard interaction, information density, productivity

**Key Requirements:**
- **Multi-Column Layouts**: Efficient use of horizontal space
- **Hover States**: Rich hover interactions and tooltips
- **Keyboard Navigation**: Full keyboard accessibility
- **Dense Information**: Tables, detailed forms, comprehensive dashboards
- **Multiple Panels**: Side-by-side content areas

---

## 📐 Responsive Breakpoint System

### Breakpoint Strategy
```css
/* Mobile First Approach */
/* Base styles: Mobile (320px+) */
.container {
  padding: 16px;
  max-width: 100%;
}

/* Small Mobile (375px+) */
@media (min-width: 375px) {
  .container {
    padding: 20px;
  }
}

/* Large Mobile (414px+) */
@media (min-width: 414px) {
  .container {
    padding: 24px;
  }
}

/* Tablet (768px+) */
@media (min-width: 768px) {
  .container {
    padding: 32px;
    max-width: 1200px;
    margin: 0 auto;
  }
}

/* Laptop (1024px+) */
@media (min-width: 1024px) {
  .container {
    padding: 40px;
  }
}

/* Desktop (1280px+) */
@media (min-width: 1280px) {
  .container {
    padding: 48px;
  }
}

/* Large Desktop (1536px+) */
@media (min-width: 1536px) {
  .container {
    padding: 64px;
    max-width: 1400px;
  }
}
```

### Tailwind CSS Responsive Classes
```css
/* Mobile-first responsive utilities */
.responsive-grid {
  @apply grid grid-cols-1 gap-4;
  @apply md:grid-cols-2 md:gap-6;
  @apply lg:grid-cols-3 lg:gap-8;
  @apply xl:grid-cols-4;
}

.responsive-text {
  @apply text-sm leading-5;
  @apply md:text-base md:leading-6;
  @apply lg:text-lg lg:leading-7;
}

.responsive-padding {
  @apply p-4;
  @apply md:p-6;
  @apply lg:p-8;
}
```

---

## 🎨 Interface-Specific Responsive Design

### 1. Admin Dashboard - Responsive Layout

#### Mobile Layout (320px - 767px)
```
┌─────────────────────┐
│     Top Header      │ ← Fixed header with hamburger menu
├─────────────────────┤
│                     │
│   Main Content      │ ← Full-width, single column
│   (Stacked Cards)   │ ← Vertical card stack
│                     │
│                     │
├─────────────────────┤
│   Bottom Nav Bar    │ ← Fixed bottom navigation
└─────────────────────┘
```

#### Laptop Layout (1024px+)
```
┌─────────────────────────────────────────┐
│              Top Header                 │ ← Full-width header
├───────────┬─────────────────────────────┤
│           │                             │
│  Sidebar  │        Main Content         │ ← Sidebar + main area
│   Menu    │     (Multi-column Grid)     │ ← Rich dashboard layout
│           │                             │
│           │                             │
└───────────┴─────────────────────────────┘
```

#### Responsive Components:
```jsx
// Responsive Sidebar
const Sidebar = () => (
  <aside className="
    fixed inset-y-0 left-0 z-50 w-64 bg-gray-900 transform transition-transform duration-300
    -translate-x-full lg:translate-x-0 lg:static lg:inset-0
  ">
    {/* Sidebar content */}
  </aside>
);

// Responsive Dashboard Grid
const DashboardGrid = () => (
  <div className="
    grid grid-cols-1 gap-4 p-4
    md:grid-cols-2 md:gap-6 md:p-6
    lg:grid-cols-3 lg:gap-8 lg:p-8
    xl:grid-cols-4
  ">
    {/* Dashboard cards */}
  </div>
);
```

### 2. Merchant Interface - Responsive Design

#### Mobile-First Product Management
```jsx
// Mobile: Stacked layout
// Tablet: 2-column layout  
// Desktop: 3-column layout with sidebar

const ProductGrid = () => (
  <div className="
    space-y-4 p-4
    md:grid md:grid-cols-2 md:gap-6 md:space-y-0 md:p-6
    lg:grid-cols-3 lg:gap-8 lg:p-8
  ">
    {products.map(product => (
      <ProductCard key={product.id} product={product} />
    ))}
  </div>
);
```

#### Responsive Navigation
```jsx
// Mobile: Bottom tab bar
// Desktop: Top navigation with dropdowns

const Navigation = () => (
  <>
    {/* Mobile Bottom Navigation */}
    <nav className="
      fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 z-50
      lg:hidden
    ">
      <div className="flex justify-around py-2">
        {/* Navigation items */}
      </div>
    </nav>

    {/* Desktop Top Navigation */}
    <nav className="
      hidden lg:flex lg:items-center lg:justify-between
      bg-white border-b border-gray-200 px-6 py-4
    ">
      {/* Desktop navigation items */}
    </nav>
  </>
);
```

### 3. Customer Interface - E-commerce Responsive Design

#### Mobile Shopping Experience
```jsx
// Mobile-optimized product browsing
const ProductListing = () => (
  <div className="
    grid grid-cols-2 gap-2 p-2
    md:grid-cols-3 md:gap-4 md:p-4
    lg:grid-cols-4 lg:gap-6 lg:p-6
    xl:grid-cols-5
  ">
    {/* Product cards optimized for each breakpoint */}
  </div>
);

// Responsive product details
const ProductDetails = () => (
  <div className="
    space-y-6 p-4
    lg:grid lg:grid-cols-2 lg:gap-8 lg:space-y-0 lg:p-8
  ">
    <ProductImages />
    <ProductInfo />
  </div>
);
```

---

## 🔧 Technical Implementation

### CSS Grid & Flexbox Strategy
```css
/* Responsive Grid System */
.responsive-container {
  display: grid;
  grid-template-columns: 1fr;
  gap: 1rem;
  padding: 1rem;
}

@media (min-width: 768px) {
  .responsive-container {
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 1.5rem;
    padding: 1.5rem;
  }
}

@media (min-width: 1024px) {
  .responsive-container {
    grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
    gap: 2rem;
    padding: 2rem;
  }
}

/* Responsive Flexbox Navigation */
.nav-container {
  display: flex;
  flex-direction: column;
}

@media (min-width: 768px) {
  .nav-container {
    flex-direction: row;
    justify-content: space-between;
    align-items: center;
  }
}
```

### React Responsive Hooks
```jsx
// Custom hook for responsive behavior
const useResponsive = () => {
  const [screenSize, setScreenSize] = useState('mobile');
  
  useEffect(() => {
    const checkScreenSize = () => {
      if (window.innerWidth >= 1024) setScreenSize('desktop');
      else if (window.innerWidth >= 768) setScreenSize('tablet');
      else setScreenSize('mobile');
    };
    
    checkScreenSize();
    window.addEventListener('resize', checkScreenSize);
    return () => window.removeEventListener('resize', checkScreenSize);
  }, []);
  
  return screenSize;
};

// Usage in components
const Dashboard = () => {
  const screenSize = useResponsive();
  
  return (
    <div className={`
      ${screenSize === 'mobile' ? 'p-4' : 'p-8'}
      ${screenSize === 'desktop' ? 'grid grid-cols-4 gap-8' : 'space-y-4'}
    `}>
      {/* Responsive content */}
    </div>
  );
};
```

---

## 📊 Performance Optimization for Mobile

### Image Optimization
```jsx
// Responsive images with Next.js
import Image from 'next/image';

const ResponsiveImage = ({ src, alt }) => (
  <Image
    src={src}
    alt={alt}
    sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
    style={{ width: '100%', height: 'auto' }}
    priority={false}
    loading="lazy"
  />
);
```

### Code Splitting for Mobile
```jsx
// Lazy load heavy components on mobile
import { lazy, Suspense } from 'react';

const HeavyChart = lazy(() => import('./HeavyChart'));

const Dashboard = () => {
  const isMobile = useResponsive() === 'mobile';
  
  return (
    <div>
      {!isMobile && (
        <Suspense fallback={<ChartSkeleton />}>
          <HeavyChart />
        </Suspense>
      )}
    </div>
  );
};
```

---

## ✅ Responsive Testing Checklist

### Mobile Testing (320px - 767px)
- [ ] All touch targets are minimum 44px × 44px
- [ ] Text is readable without zooming (minimum 16px)
- [ ] Navigation is thumb-friendly
- [ ] Forms are easy to fill on mobile keyboards
- [ ] Images load quickly and scale properly
- [ ] No horizontal scrolling required
- [ ] Bottom navigation doesn't interfere with content

### Tablet Testing (768px - 1023px)
- [ ] Layout adapts smoothly from mobile
- [ ] Touch targets remain accessible
- [ ] Content utilizes available space efficiently
- [ ] Navigation transitions work smoothly
- [ ] Modals and overlays are appropriately sized

### Laptop/Desktop Testing (1024px+)
- [ ] Multi-column layouts work properly
- [ ] Hover states are implemented
- [ ] Keyboard navigation is fully functional
- [ ] Content doesn't become too wide on large screens
- [ ] All interactive elements are accessible via mouse and keyboard

### Cross-Device Testing
- [ ] Consistent branding and visual hierarchy
- [ ] Smooth transitions between breakpoints
- [ ] No layout shifts during loading
- [ ] Performance is optimized for each device type
- [ ] Accessibility standards met across all devices

---

## 🎯 Mobile-First Development Workflow

### 1. Design Mobile First
- Start with 320px mobile design
- Focus on core functionality and content
- Ensure touch-friendly interactions
- Optimize for thumb navigation

### 2. Progressive Enhancement
- Add tablet-specific enhancements at 768px
- Implement desktop features at 1024px
- Enhance with hover states and keyboard shortcuts
- Add advanced functionality for larger screens

### 3. Test Continuously
- Test on real devices, not just browser dev tools
- Use tools like BrowserStack for cross-device testing
- Monitor performance on slower mobile networks
- Validate accessibility across all breakpoints

This comprehensive responsive design approach ensures our multi-agent e-commerce platform delivers exceptional user experiences across all devices, with particular excellence on mobile phones and laptops.
