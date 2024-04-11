// Navbar.js

import React, { useState, useEffect } from 'react';
import './Navbar.css';
import Logo from './logo.png';

const steps = ['Dataset', 'Matchers', 'Fairness', 'Resolutions'];

const Navbar = ({ step, onNext, onBack, disableNext }) => {
    const [expanded, setExpanded] = useState(false);
    const [opacityAnimationDone, setOpacityAnimationDone] = useState(false);

    useEffect(() => {
        // Start the opacity animation
        const opacityTimeout = setTimeout(() => {
            setOpacityAnimationDone(true);
        }, 300);

        // Start the width expansion animation
        const widthTimeout = setTimeout(() => {
            setExpanded(true);
        }, 2000); // Wait for 2 seconds after opacity animation completes

        return () => {
            clearTimeout(opacityTimeout);
            clearTimeout(widthTimeout);
        };
    }, []);

    const isStepFirst = step === 1;
    const isStepLast = step === steps.length;

    const renderSteps = () => {
        return steps.map((currentStep, index) => (
            <span key={index + 1} className={`step ${index + 1 === step ? 'active' : ''}`}>
                {index > 0 && <span>></span>} {currentStep}
            </span>
        ));
    };

    return (
        <div className={`navbar ${expanded ? 'expanded' : ''} ${opacityAnimationDone ? 'opaque' : ''}`}>
            <div className="navbar-left">
                <img className="logo" src={Logo} alt="FairEM" />
            </div>
            <div className="navbar-center">
                <div className="step-indicator">{renderSteps()}</div>
            </div>
            <div className="navbar-right">
                <div className="navigation-buttons-div">
                    {!isStepFirst && <button onClick={onBack}>Previous</button>}
                    {!isStepLast && <button disabled={disableNext} onClick={onNext}>Next</button>}
                </div>
            </div>
        </div>
    );
};

export default Navbar;
