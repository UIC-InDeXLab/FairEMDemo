import React, {useState} from 'react';
import './SortableTable.css';
import {Icon} from "@iconify/react";
import {toTitleCase} from "./Utils";

const SortableTable = ({tableData, title,  iconTitle = "tabler:ruler-measure"}) => {
    const [sortConfig, setSortConfig] = useState({key: null, direction: 'asc'});

    if (!tableData || Object.keys(tableData).length === 0) {
        return <div>No data available</div>;
    }

    const {columns, data} = tableData;

    if (!columns || columns.length === 0 || !data ) {
        return <div>No data available</div>;
    }

    const sortedData = [...data].sort((a, b) => {
        if (sortConfig.key) {
            const aValue = a[columns.indexOf(sortConfig.key)];
            const bValue = b[columns.indexOf(sortConfig.key)];
            if (aValue < bValue) {
                return sortConfig.direction === 'asc' ? -1 : 1;
            }
            if (aValue > bValue) {
                return sortConfig.direction === 'asc' ? 1 : -1;
            }
        }
        return 0;
    });

    const requestSort = (key) => {
        let direction = 'asc';
        if (sortConfig.key === key && sortConfig.direction === 'asc') {
            direction = 'desc';
        }
        setSortConfig({key, direction});
    };

    return (
        <div className="sortable-table-div">
            <h3><Icon inline={true} icon={iconTitle}/> {toTitleCase(title)}</h3>
            <table className="sortable-table">
                <thead>
                <tr>
                    {columns.map((column) => (
                        <th key={column} onClick={() => requestSort(column)}>
                            {toTitleCase(column)}
                            {sortConfig.key === column && (
                                <span>{sortConfig.direction === 'asc' ? ' ↓' : ' ↑'}</span>
                            )}
                        </th>
                    ))}
                </tr>
                </thead>
                <tbody>
                {sortedData.map((row, rowIndex) => (
                    <tr key={rowIndex}>
                        {row.map((value, colIndex) => (
                            <td key={colIndex}>{value}</td>
                        ))}
                    </tr>
                ))}
                </tbody>
            </table>
        </div>
    );
};

export default SortableTable;
