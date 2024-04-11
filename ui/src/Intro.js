// Intro.js

import React, { useState } from 'react';
import './intro.css';
import Logo from './logo.png';

function Intro({ onNext }) {
    const [fadeOut, setFadeOut] = useState(false);

    const handleClick = () => {
        setFadeOut(true);
        // Execute onNext function after the transition is complete
        setTimeout(() => onNext(), 1600); // Assuming transition duration is 2s
    };

    return (
        <div className={`intro-div ${fadeOut ? 'fade-out' : ''}`}>
            <div className="intro-content">
                <h1 className="intro-title">FairEM360</h1>
                <p className="intro-description">A Suite For Unfairness Detection, Explanation and Resolution in Entity Matching Tasks</p>
                <button className="intro-button" onClick={handleClick}>Get Started</button>
            </div>
            <div className="intro-image">
                <img className="logo-img" src={Logo} alt="Your Company Logo"/>
            </div>
        </div>
    );
}

export default Intro;
