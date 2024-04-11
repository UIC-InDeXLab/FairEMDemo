import React, {useState} from 'react';
import './SortableTable.css';
import {Icon} from "@iconify/react";

const SortableTable = ({data, columns, title, iconTitle = "tabler:ruler-measure" }) => {
    const [sortConfig, setSortConfig] = useState({key: null, direction: 'asc'});

    const sortedData = [...data].sort((a, b) => {
        if (sortConfig.key) {
            if (a[sortConfig.key] < b[sortConfig.key]) {
                return sortConfig.direction === 'asc' ? -1 : 1;
            }
            if (a[sortConfig.key] > b[sortConfig.key]) {
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
            <h3><Icon inline={true} icon={iconTitle}/> {title}</h3>
            <table className="sortable-table">
                <thead>
                <tr>
                    {columns.map((column) => (
                        <th key={column.key} onClick={() => requestSort(column.key)}>
                            {column.label}
                            {sortConfig.key === column.key && (
                                <span>{sortConfig.direction === 'asc' ? ' ↓' : ' ↑'}</span>
                            )}
                        </th>
                    ))}
                </tr>
                </thead>
                <tbody>
                {sortedData.map((item, index) => (
                    <tr key={index}>
                        {columns.map((column) => (
                            <td key={column.key}>{item[column.key]}</td>
                        ))}
                    </tr>
                ))}
                </tbody>
            </table>
        </div>

    );
};

export default SortableTable;
