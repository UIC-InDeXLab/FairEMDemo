import React, {useEffect, useRef, useState} from 'react';
import axios from 'axios';
import {BASE_BACKEND_URL} from './api';
import './DatasetSelection.css';
import {Icon} from "@iconify/react";

function DatasetSelection({setDatasetId, setDisableNext, onNext}) {
    const [templates, setTemplates] = useState([]);
    const [selectedTemplate, setSelectedTemplate] = useState(null);
    const [uploadStatus, setUploadStatus] = useState(null);
    const [scoreFile, setScoreFile] = useState(null);
    const [testFile, setTestFile] = useState(null);
    const [scoreTestUploadStatus, setScoreTestUploadStatus] = useState(null);
    const [file, setFile] = useState(null);
    const fileInputRef = useRef(null);
    const scoreFileRef = useRef(null);
    const testFileRef = useRef(null);

    const fetchTemplates = async () => {
        try {
            const response = await axios.get(`${BASE_BACKEND_URL}/v1/datasets/`);
            setTemplates(response.data.datasets);
        } catch (error) {
            console.error('Error fetching datasets:', error);
        }
    };

    useEffect(() => {
        setDisableNext(true);
        fetchTemplates();
    }, []);

    function resetDatasetFile() {
        setFile(null);
        fileInputRef.current.value = null;
        setUploadStatus(null);
    }

    const handleTemplateChange = (event) => {
        const selectedTemplate = event.target.value;
        setSelectedTemplate(selectedTemplate);
        setDatasetId(selectedTemplate);
        resetDatasetFile();
        resetScoreAndTestFile();
        setDisableNext(false);
    };

    function resetScoreAndTestFile() {
        setScoreFile(null);
        setTestFile(null);
        scoreFileRef.current.value = null;
        testFileRef.current.value = null;
        setScoreTestUploadStatus(null);
    }

    function resetTemplateSelection() {
        setSelectedTemplate(null);
    }

    const handleFileChange = async (event) => {
        const selectedFile = event.target.files[0];
        setFile(selectedFile);
        resetTemplateSelection();
        resetScoreAndTestFile();
        setUploadStatus('Uploading dataset...');
        await handleFileUpload(selectedFile);
        setUploadStatus('File uploaded successfully.');
        setDisableNext(false);
    };

    const handleScoreFileChange = async (event) => {
        const selectedFile = event.target.files[0];
        setScoreFile(selectedFile);
        resetDatasetFile();
        resetTemplateSelection();

        if (selectedFile && testFile) {
            setScoreTestUploadStatus('Uploading files...');
            await handleFileUpload(selectedFile);
            await handleFileUpload(testFile);
            setScoreTestUploadStatus('Files uploaded successfully.');
            setDisableNext(false);
        }
    };

    const handleTestFileChange = async (event) => {
        const selectedFile = event.target.files[0];
        setTestFile(selectedFile);
        resetDatasetFile();
        resetTemplateSelection();

        if (selectedFile && scoreFile) {
            setScoreTestUploadStatus('Uploading files...');
            await handleFileUpload(scoreFile);
            await handleFileUpload(selectedFile);
            setScoreTestUploadStatus('Files uploaded successfully.');
            setDisableNext(false);
        }
    };

    const handleFileUpload = async (selectedFile) => {
        if (!selectedFile) {
            console.error('Please select a file');
            return;
        }

        const formData = new FormData();
        formData.append('file', selectedFile);

        const response = await axios.post(`${BASE_BACKEND_URL}/v1/datasets/`, formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        });

        setDatasetId(response.data.id);
    };

    return (
        <div className="dataset-div">
            <h2><Icon inline={true} icon="fluent:data-usage-settings-16-regular"/> Dataset</h2>
            <p>This page allows you to define the data you want to use for entity matching. You have three options to choose from, uploading your own dataset, using one of the existing datasets or uploading the results of your own matcher, the test and scores files.</p>
            <div className="dataset-options-div">
                <div className="template-dataset-div">
                    <h3>Select an Existing Dataset:</h3>
                    {templates.map((template) => (
                        <label key={template.name}>
                            <input
                                type="radio"
                                name="template-dataset" // Group radio buttons
                                value={template.name}
                                onChange={handleTemplateChange}
                                checked={selectedTemplate === template.name}
                            />
                            <b> {template.name}</b>
                            <small><p>{template.description}</p>
                                <b>Sensitive Attribute:</b> {template.sensitive_attribute}</small>
                        </label>
                    ))}
                </div>
                <div className="upload-section">
                    <div className="upload-div">
                        <h3>Upload a Dataset:</h3>
                        <label>Dataset CSV:</label>
                        <input type="file" ref={fileInputRef} onChange={handleFileChange} className="file-input"/>
                        {uploadStatus && <p className="upload-status">{uploadStatus}</p>}
                    </div>
                    <div className="without-training-div">
                        <h3>Upload Scores and Test Dataset:</h3>
                        <label>Score File:</label>
                        <input type="file" ref={scoreFileRef} onChange={handleScoreFileChange} className="file-input"/>
                        <label>Test File:</label>
                        <input type="file" ref={testFileRef} onChange={handleTestFileChange} className="file-input"/>
                        {scoreTestUploadStatus && <p className="upload-status">{scoreTestUploadStatus}</p>}

                    </div>
                </div>
            </div>
        </div>
    );
}

export default DatasetSelection;
