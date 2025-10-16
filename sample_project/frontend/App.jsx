// Comprehensive React task management application demonstrating modern patterns
import React, { useState, useEffect } from 'react';
import './App.css';

interface Task {
  id: string;
  title: string;
  description: string;
  status: 'todo' | 'in_progress' | 'done';
  priority: 'low' | 'medium' | 'high';
  assignee_id?: string;
  project_id: string;
  created_at: string;
  updated_at: string;
}

interface Project {
  id: string;
  name: string;
  description: string;
  status: 'active' | 'completed' | 'archived';
  tags: string[];
  created_at: string;
}

function App() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProject, setSelectedProject] = useState<string>('');
  const [newTaskTitle, setNewTaskTitle] = useState('');
  const [newTaskDescription, setNewTaskDescription] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      // Mock API calls - in real app these would fetch from backend
      const mockTasks: Task[] = [
        {
          id: '1',
          title: 'Implement user authentication',
          description: 'Add login/logout functionality with JWT tokens',
          status: 'in_progress',
          priority: 'high',
          project_id: '1',
          created_at: '2024-01-15T10:00:00Z',
          updated_at: '2024-01-16T14:30:00Z',
        },
        {
          id: '2',
          title: 'Design database schema',
          description: 'Create ER diagram and define table relationships',
          status: 'done',
          priority: 'medium',
          project_id: '1',
          created_at: '2024-01-10T09:00:00Z',
          updated_at: '2024-01-12T16:45:00Z',
        },
      ];

      const mockProjects: Project[] = [
        {
          id: '1',
          name: 'Task Management System',
          description: 'A comprehensive task and project management application',
          status: 'active',
          tags: ['react', 'typescript', 'api'],
          created_at: '2024-01-01T00:00:00Z',
        },
      ];

      setTasks(mockTasks);
      setProjects(mockProjects);
    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      setLoading(false);
    }
  };

  const createTask = async () => {
    if (!newTaskTitle.trim()) return;

    const newTask: Task = {
      id: Date.now().toString(),
      title: newTaskTitle,
      description: newTaskDescription,
      status: 'todo',
      priority: 'medium',
      project_id: selectedProject || '1',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };

    setTasks(prev => [...prev, newTask]);
    setNewTaskTitle('');
    setNewTaskDescription('');
  };

  const updateTaskStatus = async (taskId: string, status: Task['status']) => {
    setTasks(prev =>
      prev.map(task =>
        task.id === taskId
          ? { ...task, status, updated_at: new Date().toISOString() }
          : task
      )
    );
  };

  const getStatusColor = (status: Task['status']) => {
    switch (status) {
      case 'done': return '#10b981';
      case 'in_progress': return '#f59e0b';
      default: return '#6b7280';
    }
  };

  const getPriorityColor = (priority: Task['priority']) => {
    switch (priority) {
      case 'high': return '#ef4444';
      case 'medium': return '#f59e0b';
      default: return '#10b981';
    }
  };

  if (loading) {
    return <div className="loading">Loading...</div>;
  }

  return (
    <div className="app">
      <header className="header">
        <h1>Task Management System</h1>
        <p>Organize your projects and tasks efficiently</p>
      </header>

      <div className="content">
        <div className="projects-section">
          <h2>Projects</h2>
          <div className="projects-grid">
            {projects.map(project => (
              <div key={project.id} className="project-card">
                <h3>{project.name}</h3>
                <p>{project.description}</p>
                <div className="project-tags">
                  {project.tags.map(tag => (
                    <span key={tag} className="tag">{tag}</span>
                  ))}
                </div>
                <span className={`status status-${project.status}`}>
                  {project.status}
                </span>
              </div>
            ))}
          </div>
        </div>

        <div className="tasks-section">
          <div className="tasks-header">
            <h2>Tasks</h2>
            <div className="task-form">
              <input
                type="text"
                placeholder="Task title"
                value={newTaskTitle}
                onChange={(e) => setNewTaskTitle(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && createTask()}
              />
              <textarea
                placeholder="Task description (optional)"
                value={newTaskDescription}
                onChange={(e) => setNewTaskDescription(e.target.value)}
                rows={2}
              />
              <button onClick={createTask}>Add Task</button>
            </div>
          </div>

          <div className="tasks-grid">
            {tasks.map(task => (
              <div key={task.id} className="task-card">
                <div className="task-header">
                  <h3>{task.title}</h3>
                  <span
                    className="priority-badge"
                    style={{ backgroundColor: getPriorityColor(task.priority) }}
                  >
                    {task.priority}
                  </span>
                </div>
                {task.description && (
                  <p className="task-description">{task.description}</p>
                )}
                <div className="task-footer">
                  <select
                    value={task.status}
                    onChange={(e) => updateTaskStatus(task.id, e.target.value as Task['status'])}
                    style={{ backgroundColor: getStatusColor(task.status) }}
                  >
                    <option value="todo">To Do</option>
                    <option value="in_progress">In Progress</option>
                    <option value="done">Done</option>
                  </select>
                  <span className="task-date">
                    {new Date(task.created_at).toLocaleDateString()}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
